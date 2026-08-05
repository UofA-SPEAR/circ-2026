"""Small, dependable operator panel for the CIRC GPS task workflow."""

import json
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger


SERVICE_ACTIONS = {
    "Reload waypoints": "gps/mission/reload_waypoints",
    "Previous gate": "gps/mission/previous_waypoint",
    "Next gate": "gps/mission/next_waypoint",
    "Start recording": "gps/mission/start_recording",
    "Stop recording": "gps/mission/stop_recording",
    "Capture site": "gps/mission/capture_site",
    "Capture landmark": "gps/mission/capture_landmark",
}


class GpsMissionPanelNode(Node):
    """Bridge mission status and controls to a Qt widget."""

    def __init__(self, panel) -> None:
        super().__init__("gps_mission_panel")
        self._panel = panel
        self._subscription = self.create_subscription(
            String,
            "gps/mission/status",
            self._status_callback,
            10,
        )
        self._clients = {
            label: self.create_client(Trigger, service)
            for label, service in SERVICE_ACTIONS.items()
        }

    def _status_callback(self, message: String) -> None:
        try:
            self._panel.update_status(json.loads(message.data))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            self._panel.show_result(f"Invalid mission status: {error}", False)

    def invoke(self, label: str) -> None:
        client = self._clients[label]
        if not client.service_is_ready():
            self._panel.show_result(
                f"{SERVICE_ACTIONS[label]} is unavailable",
                False,
            )
            return
        self._panel.show_result(f"Running: {label}...", True)
        future = client.call_async(Trigger.Request())
        future.add_done_callback(
            lambda completed: self._service_complete(label, completed)
        )

    def _service_complete(self, label, future) -> None:
        try:
            response = future.result()
            self._panel.show_result(
                f"{label}: {response.message}",
                response.success,
            )
        except Exception as error:
            self._panel.show_result(f"{label} failed: {error}", False)


class GpsMissionPanel(QWidget):
    """Display GPS health and expose deliberate mission-state controls."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SPEAR GPS Mission")
        self.setMinimumWidth(520)
        self._node = None
        self._values = {}

        layout = QVBoxLayout(self)
        status_group = QGroupBox("Live GPS mission status")
        status_layout = QFormLayout(status_group)
        fields = (
            ("fix", "GPS fix"),
            ("quality", "Satellites / HDOP"),
            ("waypoint", "Active gate"),
            ("target", "Target coordinate"),
            ("guidance", "Distance / bearing"),
            ("approach", "Required gate heading"),
            ("recording", "Recording"),
            ("session", "Session path"),
        )
        for key, title in fields:
            label = QLabel("waiting for rover...")
            label.setTextInteractionFlags(label.textInteractionFlags())
            label.setWordWrap(True)
            self._values[key] = label
            status_layout.addRow(title, label)
        layout.addWidget(status_group)

        controls = QGroupBox("Operator controls")
        controls_layout = QGridLayout(controls)
        for index, label in enumerate(SERVICE_ACTIONS):
            button = QPushButton(label)
            button.clicked.connect(
                lambda checked=False, action=label: self._invoke(action)
            )
            controls_layout.addWidget(button, index // 2, index % 2)
        layout.addWidget(controls)

        self._result = QLabel(
            "Start the rover launch with the task waypoint CSV configured."
        )
        self._result.setWordWrap(True)
        layout.addWidget(self._result)

    def set_node(self, node: GpsMissionPanelNode) -> None:
        self._node = node

    @staticmethod
    def _number(value, digits=1, suffix=""):
        if value is None:
            return "--"
        return f"{float(value):.{digits}f}{suffix}"

    def update_status(self, status) -> None:
        fix_valid = bool(status.get("fix_valid"))
        self._values["fix"].setText(
            "VALID" if fix_valid else "NO FIX / STALE"
        )
        self._values["fix"].setStyleSheet(
            "color: #32cd72; font-weight: bold;"
            if fix_valid
            else "color: #ff5c5c; font-weight: bold;"
        )
        satellites = status.get("satellites", 0)
        hdop = self._number(status.get("hdop"), 2)
        self._values["quality"].setText(f"{satellites} / {hdop}")
        index = status.get("waypoint_index", 0)
        count = status.get("waypoint_count", 0)
        target = status.get("target") or "none loaded"
        self._values["waypoint"].setText(f"{index}/{count}: {target}")
        latitude = status.get("target_latitude")
        longitude = status.get("target_longitude")
        coordinate = "--"
        if latitude is not None and longitude is not None:
            coordinate = f"{latitude:.7f}, {longitude:.7f}"
        self._values["target"].setText(coordinate)
        distance = self._number(status.get("distance_m"), 1, " m")
        bearing = self._number(status.get("bearing_deg"), 1, "° true")
        self._values["guidance"].setText(f"{distance} / {bearing}")
        self._values["approach"].setText(
            self._number(
                status.get("approach_heading_deg"),
                1,
                "° true",
            )
        )
        recording = bool(status.get("recording"))
        self._values["recording"].setText("ACTIVE" if recording else "STOPPED")
        self._values["recording"].setStyleSheet(
            "color: #32cd72; font-weight: bold;"
            if recording
            else "color: #ffb347; font-weight: bold;"
        )
        self._values["session"].setText(status.get("session_path") or "--")

    def show_result(self, message: str, successful: bool) -> None:
        self._result.setText(message)
        color = "#32cd72" if successful else "#ff5c5c"
        self._result.setStyleSheet(f"color: {color};")

    def _invoke(self, action: str) -> None:
        if self._node is not None:
            self._node.invoke(action)


def main(args=None) -> None:
    rclpy.init(args=args)
    application = QApplication(sys.argv)
    panel = GpsMissionPanel()
    node = GpsMissionPanelNode(panel)
    panel.set_node(node)

    spin_timer = QTimer()
    spin_timer.timeout.connect(
        lambda: rclpy.spin_once(node, timeout_sec=0.0)
    )
    spin_timer.start(20)
    panel.show()
    try:
        application.exec()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
