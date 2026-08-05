"""ROS 2 operator guidance and onboard evidence recorder for CIRC GPS tasks."""

from collections import deque
from datetime import datetime, timezone
import json
import math
import time
from typing import Dict, Optional

from diagnostic_msgs.msg import DiagnosticArray
from geometry_msgs.msg import TwistStamped
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import String
from std_srvs.srv import Trigger

from .mission import (
    FixSample,
    MissionError,
    SessionRecorder,
    Waypoint,
    distance_and_bearing,
    load_waypoints_csv,
)


class GpsMissionNode(Node):
    """Guide an operator through gates and persist an offline field record."""

    def __init__(self) -> None:
        super().__init__("gps_mission")
        self.declare_parameter("waypoints_file", "")
        self.declare_parameter(
            "output_root",
            "~/.ros/spear_gps_sessions",
        )
        self.declare_parameter("session_name", "circ_competition")
        self.declare_parameter("auto_start_recording", True)
        self.declare_parameter("capture_window_sec", 10.0)
        self.declare_parameter("minimum_site_separation_m", 10.0)
        self.declare_parameter("fix_stale_after_sec", 2.0)

        self._waypoints = []
        self._waypoint_index = 0
        self._latest_fix: Optional[FixSample] = None
        self._recent_fixes = deque(maxlen=3600)
        self._diagnostic_values: Dict[str, str] = {}
        self._speed_mps = math.nan
        self._course_deg = math.nan
        self._recorder: Optional[SessionRecorder] = None
        self._start_marker_written = False
        self._site_count = 0
        self._landmark_count = 0
        self._last_geojson_export = 0.0

        status_qos = QoSProfile(depth=1)
        status_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self._status_publisher = self.create_publisher(
            String,
            "gps/mission/status",
            status_qos,
        )
        self._fix_subscription = self.create_subscription(
            NavSatFix,
            "gps/fix",
            self._fix_callback,
            qos_profile_sensor_data,
        )
        self._nmea_subscription = self.create_subscription(
            String,
            "gps/nmea",
            self._nmea_callback,
            qos_profile_sensor_data,
        )
        self._velocity_subscription = self.create_subscription(
            TwistStamped,
            "gps/velocity",
            self._velocity_callback,
            qos_profile_sensor_data,
        )
        self._diagnostic_subscription = self.create_subscription(
            DiagnosticArray,
            "/diagnostics",
            self._diagnostics_callback,
            10,
        )
        self.create_service(
            Trigger,
            "gps/mission/reload_waypoints",
            self._reload_waypoints_service,
        )
        self.create_service(
            Trigger,
            "gps/mission/next_waypoint",
            self._next_waypoint_service,
        )
        self.create_service(
            Trigger,
            "gps/mission/previous_waypoint",
            self._previous_waypoint_service,
        )
        self.create_service(
            Trigger,
            "gps/mission/start_recording",
            self._start_recording_service,
        )
        self.create_service(
            Trigger,
            "gps/mission/stop_recording",
            self._stop_recording_service,
        )
        self.create_service(
            Trigger,
            "gps/mission/capture_site",
            self._capture_site_service,
        )
        self.create_service(
            Trigger,
            "gps/mission/capture_landmark",
            self._capture_landmark_service,
        )
        self._status_timer = self.create_timer(1.0, self._publish_status)

        self._load_waypoints(log_missing=False)
        if bool(self.get_parameter("auto_start_recording").value):
            self._start_recorder()
        self._publish_status()

    def _load_waypoints(self, log_missing: bool = True) -> bool:
        path = str(self.get_parameter("waypoints_file").value).strip()
        if not path:
            if log_missing:
                self.get_logger().warning("No waypoint CSV is configured")
            self._waypoints = []
            self._waypoint_index = 0
            return False
        try:
            self._waypoints = load_waypoints_csv(path)
            self._waypoint_index = 0
            self.get_logger().info(
                f"Loaded {len(self._waypoints)} ordered waypoints from {path}"
            )
            return True
        except MissionError as error:
            self._waypoints = []
            self._waypoint_index = 0
            self.get_logger().error(str(error))
            return False

    def _start_recorder(self) -> SessionRecorder:
        if self._recorder is not None:
            return self._recorder
        self._recorder = SessionRecorder(
            str(self.get_parameter("output_root").value),
            str(self.get_parameter("session_name").value),
        )
        self._start_marker_written = False
        self.get_logger().info(
            f"Recording GPS session to {self._recorder.path}"
        )
        return self._recorder

    @staticmethod
    def _quality_value(values: Dict[str, str], key: str, default):
        try:
            return type(default)(values.get(key, default))
        except (TypeError, ValueError):
            return default

    def _fix_callback(self, message: NavSatFix) -> None:
        if (
            message.status.status < NavSatStatus.STATUS_FIX
            or not math.isfinite(message.latitude)
            or not math.isfinite(message.longitude)
            or not -90.0 <= message.latitude <= 90.0
            or not -180.0 <= message.longitude <= 180.0
        ):
            self._publish_status()
            return

        horizontal_sigma = math.nan
        if message.position_covariance_type != NavSatFix.COVARIANCE_TYPE_UNKNOWN:
            horizontal_sigma = math.sqrt(
                max(
                    0.0,
                    message.position_covariance[0],
                    message.position_covariance[4],
                )
            )
        sample = FixSample(
            received_at_utc=datetime.now(timezone.utc).isoformat(),
            monotonic_time=time.monotonic(),
            ros_stamp_sec=message.header.stamp.sec,
            ros_stamp_nanosec=message.header.stamp.nanosec,
            latitude=message.latitude,
            longitude=message.longitude,
            altitude_ellipsoid_m=message.altitude,
            horizontal_sigma_m=horizontal_sigma,
            fix_quality=self._quality_value(
                self._diagnostic_values,
                "fix_quality",
                0,
            ),
            satellites=self._quality_value(
                self._diagnostic_values,
                "satellites",
                0,
            ),
            hdop=self._quality_value(
                self._diagnostic_values,
                "hdop",
                math.nan,
            ),
            speed_mps=self._speed_mps,
            course_deg=self._course_deg,
        )
        self._latest_fix = sample
        self._recent_fixes.append(sample)
        if self._recorder is not None:
            self._recorder.append(sample)
            if not self._start_marker_written:
                self._recorder.capture("start", [sample])
                self._start_marker_written = True
        self._publish_status()

    def _nmea_callback(self, message: String) -> None:
        if self._recorder is not None:
            timestamp = datetime.now(timezone.utc).isoformat()
            self._recorder.append_nmea(timestamp, message.data)

    def _velocity_callback(self, message: TwistStamped) -> None:
        east = message.twist.linear.x
        north = message.twist.linear.y
        self._speed_mps = math.hypot(east, north)
        self._course_deg = math.degrees(math.atan2(east, north)) % 360.0

    def _diagnostics_callback(self, message: DiagnosticArray) -> None:
        for status in message.status:
            if status.name == "ultimate_gps/fix":
                self._diagnostic_values = {
                    value.key: value.value for value in status.values
                }

    def _active_waypoint(self) -> Optional[Waypoint]:
        if not self._waypoints:
            return None
        return self._waypoints[self._waypoint_index]

    def _publish_status(self) -> None:
        now = time.monotonic()
        fix_age = (
            math.inf
            if self._latest_fix is None
            else max(0.0, now - self._latest_fix.monotonic_time)
        )
        stale_after = max(
            0.2,
            float(self.get_parameter("fix_stale_after_sec").value),
        )
        fix_valid = self._latest_fix is not None and fix_age <= stale_after
        waypoint = self._active_waypoint()
        status = {
            "fix_valid": fix_valid,
            "fix_age_sec": None if not math.isfinite(fix_age) else fix_age,
            "satellites": self._quality_value(
                self._diagnostic_values,
                "satellites",
                0,
            ),
            "hdop": self._quality_value(
                self._diagnostic_values,
                "hdop",
                math.nan,
            ),
            "recording": self._recorder is not None,
            "session_path": (
                str(self._recorder.path) if self._recorder else None
            ),
            "waypoint_index": (
                self._waypoint_index + 1 if waypoint is not None else 0
            ),
            "waypoint_count": len(self._waypoints),
            "target": waypoint.name if waypoint else None,
            "target_latitude": waypoint.latitude if waypoint else None,
            "target_longitude": waypoint.longitude if waypoint else None,
            "approach_heading_deg": (
                waypoint.approach_heading_deg if waypoint else None
            ),
            "distance_m": None,
            "bearing_deg": None,
        }
        if fix_valid and waypoint is not None:
            distance, bearing = distance_and_bearing(
                self._latest_fix.latitude,
                self._latest_fix.longitude,
                waypoint.latitude,
                waypoint.longitude,
            )
            status["distance_m"] = distance
            status["bearing_deg"] = bearing

        status["hdop"] = (
            status["hdop"]
            if math.isfinite(float(status["hdop"]))
            else None
        )
        self._status_publisher.publish(
            String(data=json.dumps(status, allow_nan=False))
        )
        if self._recorder and now - self._last_geojson_export >= 1.0:
            self._recorder.export_geojson()
            self._last_geojson_export = now

    def _capture_window(self):
        if self._recorder is None:
            raise MissionError("start recording before capturing a marker")
        window = max(
            1.0,
            float(self.get_parameter("capture_window_sec").value),
        )
        cutoff = time.monotonic() - window
        samples = [
            sample
            for sample in self._recent_fixes
            if sample.monotonic_time >= cutoff
        ]
        if len(samples) < 5:
            raise MissionError("not enough valid fixes for a site capture")
        span = samples[-1].monotonic_time - samples[0].monotonic_time
        if span < 0.8 * window:
            raise MissionError(
                f"hold stationary for {window:.0f} seconds before capture"
            )
        return samples

    def _reload_waypoints_service(self, request, response):
        del request
        response.success = self._load_waypoints()
        response.message = (
            f"loaded {len(self._waypoints)} waypoints"
            if response.success
            else "waypoint reload failed; see node logs"
        )
        self._publish_status()
        return response

    def _next_waypoint_service(self, request, response):
        del request
        if not self._waypoints:
            response.success = False
            response.message = "no waypoints loaded"
        elif self._waypoint_index >= len(self._waypoints) - 1:
            response.success = False
            response.message = "already at the final waypoint"
        else:
            self._waypoint_index += 1
            response.success = True
            response.message = self._active_waypoint().name
        self._publish_status()
        return response

    def _previous_waypoint_service(self, request, response):
        del request
        if not self._waypoints:
            response.success = False
            response.message = "no waypoints loaded"
        elif self._waypoint_index == 0:
            response.success = False
            response.message = "already at the first waypoint"
        else:
            self._waypoint_index -= 1
            response.success = True
            response.message = self._active_waypoint().name
        self._publish_status()
        return response

    def _start_recording_service(self, request, response):
        del request
        if self._recorder is not None:
            response.success = False
            response.message = f"already recording to {self._recorder.path}"
        else:
            recorder = self._start_recorder()
            response.success = True
            response.message = str(recorder.path)
        self._publish_status()
        return response

    def _stop_recording_service(self, request, response):
        del request
        if self._recorder is None:
            response.success = False
            response.message = "recording is not active"
        else:
            path = self._recorder.path
            self._recorder.close()
            self._recorder = None
            response.success = True
            response.message = str(path)
        self._publish_status()
        return response

    def _capture_site_service(self, request, response):
        del request
        try:
            samples = self._capture_window()
            label = f"site_{self._site_count + 1}"
            marker = self._recorder.capture(label, samples)
            self._site_count += 1
            minimum = float(
                self.get_parameter("minimum_site_separation_m").value
            )
            previous_sites = [
                item
                for item in self._recorder.markers[:-1]
                if item.label.startswith("site_")
            ]
            distances = [
                distance_and_bearing(
                    marker.latitude,
                    marker.longitude,
                    item.latitude,
                    item.longitude,
                )[0]
                for item in previous_sites
            ]
            warning = ""
            if distances and min(distances) < minimum:
                warning = (
                    f" WARNING: only {min(distances):.1f} m from another site"
                )
                self.get_logger().warning(warning.strip())
            response.success = True
            response.message = (
                f"captured {label}: {marker.latitude:.7f},"
                f"{marker.longitude:.7f}; spread={marker.spread_m:.2f} m"
                f"{warning}"
            )
        except MissionError as error:
            response.success = False
            response.message = str(error)
        return response

    def _capture_landmark_service(self, request, response):
        del request
        try:
            samples = self._capture_window()
            label = f"landmark_{self._landmark_count + 1}"
            marker = self._recorder.capture(label, samples)
            self._landmark_count += 1
            response.success = True
            response.message = (
                f"captured {label}: {marker.latitude:.7f},"
                f"{marker.longitude:.7f}"
            )
        except MissionError as error:
            response.success = False
            response.message = str(error)
        return response

    def destroy_node(self) -> bool:
        if self._recorder is not None:
            self._recorder.close()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = GpsMissionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
