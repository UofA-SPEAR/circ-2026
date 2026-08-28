#!/usr/bin/env python3
"""ROS2 node that reads NMEA GPS data from a serial device and publishes NavSatFix."""
from __future__ import annotations

from typing import Optional

import rclpy
import serial
import pynmea2
from rclpy.node import Node
from std_msgs.msg import Float64


class GpsSerialNode(Node):
    def __init__(self) -> None:
        super().__init__("gps_serial_node")

        self.declare_parameter("port", "/dev/ttyACM0")
        self.declare_parameter("baudrate", 9600)
        self.declare_parameter("timeout", 1.0)
        port: str = self.get_parameter("port").get_parameter_value().string_value
        baudrate: int = self.get_parameter("baudrate").get_parameter_value().integer_value
        timeout: float = self.get_parameter("timeout").get_parameter_value().double_value

        self._lat_publisher = self.create_publisher(Float64, "gps/latitude", 10)
        self._lon_publisher = self.create_publisher(Float64, "gps/longitude", 10)

        try:
            self._serial = serial.Serial(port, baudrate, timeout=timeout)
        except serial.SerialException as e:
            self.get_logger().error(f"Could not open {port}: {e}")
            raise

        self.get_logger().info(f"Reading GPS data from {port} @ {baudrate} baud")

        # Poll as fast as readline() unblocks (bounded by serial timeout).
        self._timer = self.create_timer(0.0, self._poll)

    def _poll(self) -> None:
        raw = self._serial.readline()
        if not raw:
            return
        try:
            line = raw.decode("ascii", errors="replace").strip()
        except UnicodeDecodeError:
            return
        if not line:
            return

        latlon = self._parse_line(line)
        if latlon is not None:
            lat, lon = latlon
            self._lat_publisher.publish(Float64(data=lat))
            self._lon_publisher.publish(Float64(data=lon))

    def _parse_line(self, line: str) -> Optional[tuple[float, float]]:
        try:
            msg = pynmea2.parse(line)
        except pynmea2.ParseError:
            return None

        if not isinstance(msg, (pynmea2.types.talker.GGA, pynmea2.types.talker.RMC)):
            return None
        if msg.latitude == 0.0 and msg.longitude == 0.0:
            return None

        return (msg.latitude, msg.longitude)

    def destroy_node(self) -> bool:
        if hasattr(self, "_serial") and self._serial.is_open:
            self._serial.close()
        return super().destroy_node()


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node = GpsSerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()