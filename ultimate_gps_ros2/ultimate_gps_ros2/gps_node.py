"""ROS 2 serial driver for the Adafruit Ultimate GPS Breakout V3."""

from datetime import datetime
import math
import time
from typing import Dict, Optional

from builtin_interfaces.msg import Time as TimeMessage
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from geometry_msgs.msg import TwistStamped
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import NavSatFix, NavSatStatus, TimeReference
from std_msgs.msg import String
from std_srvs.srv import Trigger

from .nmea import (
    GgaFix,
    NmeaChecksumError,
    NmeaError,
    add_checksum,
    parse_gga,
    parse_pmtk_ack,
    parse_rmc,
    sentence_type,
)

try:
    import serial
except ImportError:  # pragma: no cover - depends on the target OS image
    serial = None


class UltimateGpsNode(Node):
    """Read MTK3339 NMEA data and publish standard ROS 2 messages."""

    MAX_RX_BUFFER_BYTES = 16_384
    MAX_READ_BYTES = 4_096
    RECEIVER_OUTPUT_COMMAND = (
        "PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
    )

    def __init__(self) -> None:
        super().__init__("ultimate_gps")

        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baud_rate", 9600)
        self.declare_parameter("frame_id", "gps_link")
        self.declare_parameter("velocity_frame_id", "map")
        self.declare_parameter("configure_receiver", True)
        self.declare_parameter("update_rate_hz", 5)
        self.declare_parameter("reconnect_delay_sec", 2.0)
        self.declare_parameter("stale_after_sec", 2.0)
        self.declare_parameter("uere_m", 3.0)
        self.declare_parameter("diagnostics_rate_hz", 1.0)

        self._port = str(self.get_parameter("port").value)
        self._baud_rate = int(self.get_parameter("baud_rate").value)
        self._frame_id = str(self.get_parameter("frame_id").value)
        self._velocity_frame_id = str(
            self.get_parameter("velocity_frame_id").value
        )
        self._configure_on_connect = bool(
            self.get_parameter("configure_receiver").value
        )
        self._update_rate_hz = int(
            self.get_parameter("update_rate_hz").value
        )
        self._reconnect_delay_sec = max(
            0.1,
            float(self.get_parameter("reconnect_delay_sec").value),
        )
        self._stale_after_sec = max(
            0.2,
            float(self.get_parameter("stale_after_sec").value),
        )
        self._uere_m = max(0.1, float(self.get_parameter("uere_m").value))

        diagnostics_rate = max(
            0.1,
            float(self.get_parameter("diagnostics_rate_hz").value),
        )

        self._serial = None
        self._rx_buffer = bytearray()
        self._last_connect_attempt = float("-inf")
        self._successful_connections = 0
        self._reconnect_count = 0
        self._last_serial_error = "none"
        self._last_warning_times: Dict[str, float] = {}

        self._last_sentence_time: Optional[float] = None
        self._last_gga_time: Optional[float] = None
        self._last_valid_fix_time: Optional[float] = None
        self._latest_quality = 0
        self._latest_satellites = 0
        self._latest_hdop = math.nan
        self._latest_talker = "unknown"

        self._total_sentences = 0
        self._valid_sentences = 0
        self._checksum_errors = 0
        self._parse_errors = 0
        self._decode_errors = 0
        self._buffer_overflows = 0
        self._interval_sentences = 0
        self._last_interval_time = time.monotonic()
        self._nmea_rate_hz = 0.0
        self._checksum_error_rate = 0.0

        self._expected_acks: Dict[int, Optional[bool]] = {}
        self._configuration_sent_time: Optional[float] = None
        self._receiver_config_state = (
            "not connected" if self._configure_on_connect else "disabled"
        )

        self._fix_publisher = self.create_publisher(
            NavSatFix,
            "gps/fix",
            qos_profile_sensor_data,
        )
        self._velocity_publisher = self.create_publisher(
            TwistStamped,
            "gps/velocity",
            qos_profile_sensor_data,
        )
        self._nmea_publisher = self.create_publisher(
            String,
            "gps/nmea",
            qos_profile_sensor_data,
        )
        self._time_publisher = self.create_publisher(
            TimeReference,
            "gps/time_reference",
            qos_profile_sensor_data,
        )
        self._diagnostics_publisher = self.create_publisher(
            DiagnosticArray,
            "/diagnostics",
            10,
        )
        self._reconfigure_service = self.create_service(
            Trigger,
            "gps/reconfigure",
            self._handle_reconfigure,
        )

        self._poll_timer = self.create_timer(0.01, self._poll_serial)
        self._diagnostics_timer = self.create_timer(
            1.0 / diagnostics_rate,
            self._publish_diagnostics,
        )

        if serial is None:
            self.get_logger().error(
                "pyserial is unavailable; install it with "
                "'sudo apt install python3-serial'"
            )
        else:
            self._connect()

    def _warn_throttled(
        self,
        key: str,
        message: str,
        interval_sec: float = 10.0,
    ) -> None:
        now = time.monotonic()
        last_warning = self._last_warning_times.get(key, float("-inf"))
        if now - last_warning >= interval_sec:
            self.get_logger().warning(message)
            self._last_warning_times[key] = now

    def _connect(self) -> None:
        if serial is None:
            return

        self._last_connect_attempt = time.monotonic()
        try:
            serial_port = serial.Serial(
                port=self._port,
                baudrate=self._baud_rate,
                timeout=0,
                write_timeout=0.5,
            )
            serial_port.reset_input_buffer()
            self._serial = serial_port
            self._rx_buffer.clear()
            self._successful_connections += 1
            if self._successful_connections > 1:
                self._reconnect_count += 1
            self._last_serial_error = "none"
            self.get_logger().info(
                f"Connected to Ultimate GPS on {self._port} at "
                f"{self._baud_rate} baud"
            )
            if self._configure_on_connect:
                self._configure_receiver()
            else:
                self._receiver_config_state = "disabled"
        except (serial.SerialException, OSError) as error:
            self._serial = None
            self._last_serial_error = str(error)
            self._warn_throttled(
                "connect",
                f"Cannot open GPS serial port {self._port}: {error}; retrying",
            )

    def _disconnect(self, error: Exception) -> None:
        self._last_serial_error = str(error)
        self._warn_throttled(
            "serial_io",
            f"GPS serial I/O failed: {error}; reconnecting",
        )
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:  # pragma: no cover - best-effort device cleanup
                pass
        self._serial = None
        self._rx_buffer.clear()
        if self._configure_on_connect:
            self._receiver_config_state = "not connected"

    def _validated_update_rate(self) -> int:
        if self._update_rate_hz in (1, 2, 5):
            return self._update_rate_hz
        self._warn_throttled(
            "update_rate",
            "RMC+GGA at 9600 baud supports 1, 2, or 5 Hz; using 5 Hz",
            interval_sec=60.0,
        )
        return 5

    def _configure_receiver(self) -> None:
        if self._serial is None:
            raise RuntimeError("cannot configure a disconnected receiver")

        update_rate = self._validated_update_rate()
        period_ms = 1000 // update_rate
        commands = {
            314: self.RECEIVER_OUTPUT_COMMAND,
            220: f"PMTK220,{period_ms}",
        }
        self._expected_acks = {command_id: None for command_id in commands}
        self._configuration_sent_time = time.monotonic()
        self._receiver_config_state = "waiting for acknowledgement"
        try:
            for command in commands.values():
                self._serial.write(add_checksum(command))
            self._serial.flush()
            self.get_logger().info(
                f"Requested RMC+GGA output at {update_rate} Hz"
            )
        except (serial.SerialException, OSError) as error:
            self._disconnect(error)

    def _handle_reconfigure(self, request, response):
        del request
        if self._serial is None:
            response.success = False
            response.message = "GPS serial port is not connected"
            return response
        try:
            self._configure_receiver()
            response.success = self._serial is not None
            response.message = (
                "Receiver configuration sent; awaiting PMTK acknowledgements"
                if response.success
                else "Receiver configuration failed during serial write"
            )
        except RuntimeError as error:
            response.success = False
            response.message = str(error)
        return response

    def _poll_serial(self) -> None:
        if serial is None:
            return
        if self._serial is None:
            elapsed = time.monotonic() - self._last_connect_attempt
            if elapsed >= self._reconnect_delay_sec:
                self._connect()
            return

        try:
            bytes_waiting = int(self._serial.in_waiting)
            if bytes_waiting <= 0:
                return
            chunk = self._serial.read(min(bytes_waiting, self.MAX_READ_BYTES))
            if not chunk:
                return
            self._rx_buffer.extend(chunk)
            if len(self._rx_buffer) > self.MAX_RX_BUFFER_BYTES:
                self._rx_buffer.clear()
                self._buffer_overflows += 1
                self._warn_throttled(
                    "rx_buffer",
                    "GPS receive buffer overflowed and was cleared",
                )
                return
            self._consume_complete_lines()
        except (serial.SerialException, OSError) as error:
            self._disconnect(error)

    def _consume_complete_lines(self) -> None:
        while b"\n" in self._rx_buffer:
            raw_line, _, remaining = self._rx_buffer.partition(b"\n")
            self._rx_buffer = bytearray(remaining)
            raw_line = raw_line.rstrip(b"\r")
            if not raw_line:
                continue
            try:
                sentence = raw_line.decode("ascii")
            except UnicodeDecodeError:
                self._decode_errors += 1
                continue
            self._handle_sentence(sentence)

    def _handle_sentence(self, sentence: str) -> None:
        if not sentence.startswith("$"):
            return

        now = time.monotonic()
        self._last_sentence_time = now
        self._total_sentences += 1
        self._interval_sentences += 1
        self._nmea_publisher.publish(String(data=sentence))

        try:
            message_type = sentence_type(sentence)
            self._valid_sentences += 1
            if message_type == "GGA":
                self._handle_gga(parse_gga(sentence), now)
            elif message_type == "RMC":
                self._handle_rmc(parse_rmc(sentence))
            elif message_type == "PMTK001":
                self._handle_pmtk_ack(sentence)
        except NmeaChecksumError:
            self._checksum_errors += 1
        except NmeaError:
            self._parse_errors += 1

    def _handle_gga(self, fix: GgaFix, now: float) -> None:
        self._last_gga_time = now
        self._latest_quality = fix.quality
        self._latest_satellites = fix.satellites
        self._latest_hdop = fix.hdop
        self._latest_talker = fix.talker or "unknown"
        if fix.valid:
            self._last_valid_fix_time = now

        message = NavSatFix()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self._frame_id
        message.latitude = fix.latitude
        message.longitude = fix.longitude
        message.altitude = fix.altitude_ellipsoid
        message.status.service = NavSatStatus.SERVICE_GPS

        if not fix.valid:
            message.status.status = NavSatStatus.STATUS_NO_FIX
        elif fix.quality == 1:
            message.status.status = NavSatStatus.STATUS_FIX
        else:
            message.status.status = NavSatStatus.STATUS_GBAS_FIX

        if fix.valid and math.isfinite(fix.hdop):
            horizontal_sigma = max(1.0, self._uere_m * fix.hdop)
            vertical_sigma = 2.0 * horizontal_sigma
            message.position_covariance[0] = horizontal_sigma**2
            message.position_covariance[4] = horizontal_sigma**2
            message.position_covariance[8] = vertical_sigma**2
            message.position_covariance_type = (
                NavSatFix.COVARIANCE_TYPE_APPROXIMATED
            )
        else:
            message.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
        self._fix_publisher.publish(message)

    def _handle_rmc(self, fix) -> None:
        now_message = self.get_clock().now().to_msg()
        if fix.timestamp is not None:
            time_reference = TimeReference()
            time_reference.header.stamp = now_message
            time_reference.header.frame_id = self._frame_id
            time_reference.time_ref = self._datetime_to_time_message(
                fix.timestamp
            )
            time_reference.source = "GPS"
            self._time_publisher.publish(time_reference)

        if not (
            fix.valid
            and math.isfinite(fix.speed_mps)
            and math.isfinite(fix.course_deg)
        ):
            return

        course_rad = math.radians(fix.course_deg)
        velocity = TwistStamped()
        velocity.header.stamp = now_message
        velocity.header.frame_id = self._velocity_frame_id
        # NMEA course is clockwise from true north. Convert to ROS ENU axes.
        velocity.twist.linear.x = fix.speed_mps * math.sin(course_rad)
        velocity.twist.linear.y = fix.speed_mps * math.cos(course_rad)
        self._velocity_publisher.publish(velocity)

    @staticmethod
    def _datetime_to_time_message(timestamp: datetime) -> TimeMessage:
        unix_seconds = timestamp.timestamp()
        seconds = math.floor(unix_seconds)
        nanoseconds = round((unix_seconds - seconds) * 1_000_000_000)
        if nanoseconds == 1_000_000_000:
            seconds += 1
            nanoseconds = 0
        return TimeMessage(sec=seconds, nanosec=nanoseconds)

    def _handle_pmtk_ack(self, sentence: str) -> None:
        acknowledgement = parse_pmtk_ack(sentence)
        if acknowledgement.command not in self._expected_acks:
            return
        self._expected_acks[acknowledgement.command] = (
            acknowledgement.successful
        )
        if any(value is False for value in self._expected_acks.values()):
            self._receiver_config_state = "receiver rejected a command"
        elif all(value is True for value in self._expected_acks.values()):
            self._receiver_config_state = "acknowledged"

    @staticmethod
    def _age(now: float, then: Optional[float]) -> float:
        return math.inf if then is None else max(0.0, now - then)

    @staticmethod
    def _format_float(value: float, digits: int = 2) -> str:
        return "unknown" if not math.isfinite(value) else f"{value:.{digits}f}"

    @staticmethod
    def _key(name: str, value) -> KeyValue:
        return KeyValue(key=name, value=str(value))

    def _update_interval_rates(self, now: float) -> None:
        elapsed = max(1e-6, now - self._last_interval_time)
        interval_total = self._interval_sentences
        self._nmea_rate_hz = interval_total / elapsed

        previous_error_total = getattr(self, "_previous_checksum_errors", 0)
        interval_errors = self._checksum_errors - previous_error_total
        self._checksum_error_rate = (
            interval_errors / interval_total if interval_total else 0.0
        )
        self._previous_checksum_errors = self._checksum_errors
        self._interval_sentences = 0
        self._last_interval_time = now

    def _publish_diagnostics(self) -> None:
        now = time.monotonic()
        self._update_interval_rates(now)
        if (
            self._receiver_config_state == "waiting for acknowledgement"
            and self._configuration_sent_time is not None
            and now - self._configuration_sent_time > 5.0
        ):
            self._receiver_config_state = "acknowledgement timeout"

        serial_status = DiagnosticStatus()
        serial_status.name = "ultimate_gps/serial"
        serial_status.hardware_id = self._port
        serial_status.values = [
            self._key("port", self._port),
            self._key("baud_rate", self._baud_rate),
            self._key("reconnect_count", self._reconnect_count),
            self._key("last_error", self._last_serial_error),
        ]
        if serial is None:
            serial_status.level = DiagnosticStatus.ERROR
            serial_status.message = "pyserial is not installed"
        elif self._serial is None:
            serial_status.level = DiagnosticStatus.ERROR
            serial_status.message = "serial port disconnected"
        else:
            serial_status.level = DiagnosticStatus.OK
            serial_status.message = "serial port connected"

        gga_age = self._age(now, self._last_gga_time)
        valid_fix_age = self._age(now, self._last_valid_fix_time)
        fix_status = DiagnosticStatus()
        fix_status.name = "ultimate_gps/fix"
        fix_status.hardware_id = self._port
        fix_status.values = [
            self._key("fix_quality", self._latest_quality),
            self._key("satellites", self._latest_satellites),
            self._key("hdop", self._format_float(self._latest_hdop)),
            self._key("talker", self._latest_talker),
            self._key("gga_age_sec", self._format_float(gga_age)),
            self._key(
                "valid_fix_age_sec",
                self._format_float(valid_fix_age),
            ),
        ]
        if self._serial is None:
            fix_status.level = DiagnosticStatus.ERROR
            fix_status.message = "no GPS data because serial is disconnected"
        elif gga_age > self._stale_after_sec:
            fix_status.level = DiagnosticStatus.WARN
            fix_status.message = "GGA data is stale or has not arrived"
        elif self._latest_quality <= 0:
            fix_status.level = DiagnosticStatus.WARN
            fix_status.message = "receiver is searching for a position fix"
        else:
            fix_status.level = DiagnosticStatus.OK
            fix_status.message = "valid position fix"

        stream_status = DiagnosticStatus()
        stream_status.name = "ultimate_gps/nmea_stream"
        stream_status.hardware_id = self._port
        stream_status.values = [
            self._key("nmea_rate_hz", self._format_float(self._nmea_rate_hz)),
            self._key("total_sentences", self._total_sentences),
            self._key("valid_sentences", self._valid_sentences),
            self._key("checksum_errors", self._checksum_errors),
            self._key("parse_errors", self._parse_errors),
            self._key("decode_errors", self._decode_errors),
            self._key("buffer_overflows", self._buffer_overflows),
            self._key(
                "checksum_error_percent",
                self._format_float(100.0 * self._checksum_error_rate),
            ),
            self._key("receiver_configuration", self._receiver_config_state),
        ]
        if self._checksum_error_rate > 0.1:
            stream_status.level = DiagnosticStatus.WARN
            stream_status.message = "high NMEA checksum error rate"
        elif self._receiver_config_state == "receiver rejected a command":
            stream_status.level = DiagnosticStatus.WARN
            stream_status.message = self._receiver_config_state
        elif self._receiver_config_state == "acknowledgement timeout":
            stream_status.level = DiagnosticStatus.WARN
            stream_status.message = self._receiver_config_state
        else:
            stream_status.level = DiagnosticStatus.OK
            stream_status.message = "NMEA stream healthy"

        diagnostics = DiagnosticArray()
        diagnostics.header.stamp = self.get_clock().now().to_msg()
        diagnostics.status = [serial_status, fix_status, stream_status]
        self._diagnostics_publisher.publish(diagnostics)

    def destroy_node(self) -> bool:
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:  # pragma: no cover - best-effort device cleanup
                pass
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = UltimateGpsNode()
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
