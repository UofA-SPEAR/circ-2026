"""ROS 2 serial node for factory-configured u-blox NEO-M9N receivers."""

import math
import time
from typing import Optional

from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from geometry_msgs.msg import TwistStamped
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import Float64, String, UInt32

from neo_m9n_gps.nmea import (
    GpsState,
    NmeaChecksumError,
    NmeaError,
    covariance_from_dop,
    enu_velocity,
    parse_sentence,
)
from neo_m9n_gps.serial_probe import select_serial_port


class NeoM9nGpsNode(Node):
    """Read NMEA over serial and publish standard ROS navigation messages."""

    def __init__(self) -> None:
        super().__init__('neo_m9n_gps')

        self.declare_parameter('port', 'auto')
        self.declare_parameter('baud', 38400)
        self.declare_parameter('frame_id', 'gps_link')
        self.declare_parameter('velocity_frame_id', 'map')
        self.declare_parameter('publish_raw', False)
        self.declare_parameter('poll_period_sec', 0.02)
        self.declare_parameter('reconnect_interval_sec', 2.0)
        self.declare_parameter('stale_timeout_sec', 3.0)
        self.declare_parameter('diagnostic_period_sec', 1.0)
        self.declare_parameter('uere_m', 3.0)
        self.declare_parameter('minimum_sigma_m', 1.0)
        self.declare_parameter('service_mask', 15)
        self.declare_parameter('read_chunk_size', 4096)
        self.declare_parameter(
            'auto_port_patterns',
            ['/dev/ttyACM*', '/dev/ttyUSB*', '/dev/serial/by-id/*'],
        )

        self._requested_port = str(self.get_parameter('port').value)
        self._baud = int(self.get_parameter('baud').value)
        self._frame_id = str(self.get_parameter('frame_id').value)
        self._velocity_frame_id = str(
            self.get_parameter('velocity_frame_id').value
        )
        self._publish_raw = bool(self.get_parameter('publish_raw').value)
        self._reconnect_interval = max(
            float(self.get_parameter('reconnect_interval_sec').value), 0.1
        )
        self._stale_timeout = max(
            float(self.get_parameter('stale_timeout_sec').value), 0.1
        )
        self._uere_m = max(float(self.get_parameter('uere_m').value), 0.01)
        self._minimum_sigma_m = max(
            float(self.get_parameter('minimum_sigma_m').value), 0.01
        )
        self._service_mask = int(self.get_parameter('service_mask').value)
        self._read_chunk_size = max(
            int(self.get_parameter('read_chunk_size').value), 64
        )
        self._auto_port_patterns = tuple(
            str(value)
            for value in self.get_parameter('auto_port_patterns').value
        )

        self._fix_pub = self.create_publisher(NavSatFix, 'fix', 10)
        self._velocity_pub = self.create_publisher(TwistStamped, 'velocity', 10)
        self._course_pub = self.create_publisher(Float64, 'course_deg', 10)
        self._satellites_pub = self.create_publisher(UInt32, 'satellites', 10)
        self._diagnostics_pub = self.create_publisher(
            DiagnosticArray, '/diagnostics', 10
        )
        self._raw_pub = (
            self.create_publisher(String, 'raw', 20) if self._publish_raw else None
        )

        self._serial: Optional[object] = None
        self._resolved_port = ''
        self._receive_buffer = bytearray()
        self._state = GpsState()
        self._last_connect_attempt = 0.0
        self._last_sentence_time: Optional[float] = None
        self._last_fix_time: Optional[float] = None
        self._valid_sentences = 0
        self._checksum_errors = 0
        self._parse_errors = 0
        self._serial_errors = 0
        self._last_error = ''

        poll_period = max(float(self.get_parameter('poll_period_sec').value), 0.005)
        diagnostic_period = max(
            float(self.get_parameter('diagnostic_period_sec').value), 0.1
        )
        self._poll_timer = self.create_timer(poll_period, self._poll_serial)
        self._diagnostic_timer = self.create_timer(
            diagnostic_period, self._publish_diagnostics
        )

        self.get_logger().info(
            f'NEO-M9N driver configured for {self._requested_port} at '
            f'{self._baud} baud'
        )

    def destroy_node(self) -> bool:
        """Close the serial port before node shutdown."""
        self._disconnect('node shutdown', log=False)
        return super().destroy_node()

    def _poll_serial(self) -> None:
        if self._serial is None:
            self._try_connect()
            return

        try:
            waiting = int(getattr(self._serial, 'in_waiting', 0))
            if waiting <= 0:
                return
            data = self._serial.read(min(waiting, self._read_chunk_size))
            if data:
                self._consume(data)
        except Exception as exc:  # pyserial raises several platform exceptions
            self._serial_errors += 1
            self._disconnect(f'serial read failed: {exc}')

    def _try_connect(self) -> None:
        now = time.monotonic()
        if now - self._last_connect_attempt < self._reconnect_interval:
            return
        self._last_connect_attempt = now

        try:
            import serial

            port = select_serial_port(
                self._requested_port, self._auto_port_patterns
            )
            serial_port = serial.Serial(
                port=port,
                baudrate=self._baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0,
                write_timeout=0,
            )
        except Exception as exc:
            message = str(exc)
            if message != self._last_error:
                self.get_logger().warning(f'GPS serial connection failed: {message}')
            self._last_error = message
            return

        self._serial = serial_port
        self._resolved_port = port
        self._last_error = ''
        self._receive_buffer.clear()
        self.get_logger().info(f'Connected to NEO-M9N serial port {port}')

    def _disconnect(self, reason: str, log: bool = True) -> None:
        serial_port = self._serial
        self._serial = None
        if serial_port is not None:
            try:
                serial_port.close()
            except Exception:
                pass
        self._last_error = reason
        if log:
            self.get_logger().error(reason)

    def _consume(self, data: bytes) -> None:
        self._receive_buffer.extend(data)
        if len(self._receive_buffer) > 65536:
            self._receive_buffer = self._receive_buffer[-8192:]
            self._parse_errors += 1
            self._last_error = 'receive buffer overflow; discarded old serial data'

        while b'\n' in self._receive_buffer:
            line, _, remainder = self._receive_buffer.partition(b'\n')
            self._receive_buffer = bytearray(remainder)
            text = line.decode('ascii', errors='ignore').strip('\r\x00 ')
            if text:
                self._handle_line(text)

    def _handle_line(self, text: str) -> None:
        if self._raw_pub is not None:
            self._raw_pub.publish(String(data=text))
        try:
            sentence = parse_sentence(text)
            message_type = self._state.update(sentence)
        except NmeaChecksumError as exc:
            self._checksum_errors += 1
            self._last_error = str(exc)
            return
        except NmeaError as exc:
            self._parse_errors += 1
            self._last_error = str(exc)
            return

        self._valid_sentences += 1
        self._last_sentence_time = time.monotonic()
        if message_type == 'GGA':
            self._publish_fix()
        elif message_type == 'VTG' or (
            message_type == 'RMC' and self._state.rmc_valid
        ):
            self._publish_velocity()

    def _publish_fix(self) -> None:
        message = NavSatFix()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self._frame_id
        message.status.status = (
            NavSatStatus.STATUS_FIX
            if self._state.has_fix
            else NavSatStatus.STATUS_NO_FIX
        )
        message.status.service = self._service_mask
        message.latitude = _nan_if_none(self._state.latitude_deg)
        message.longitude = _nan_if_none(self._state.longitude_deg)
        message.altitude = _nan_if_none(self._state.altitude_ellipsoid_m)
        if self._state.has_fix:
            message.position_covariance = list(
                covariance_from_dop(
                    self._state.hdop,
                    self._state.vdop,
                    self._uere_m,
                    self._minimum_sigma_m,
                )
            )
            message.position_covariance_type = (
                NavSatFix.COVARIANCE_TYPE_APPROXIMATED
            )
        else:
            message.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
        self._fix_pub.publish(message)
        self._satellites_pub.publish(UInt32(data=max(self._state.satellites, 0)))
        if self._state.has_fix:
            self._last_fix_time = time.monotonic()

    def _publish_velocity(self) -> None:
        speed = self._state.speed_mps
        course = self._state.course_deg
        if speed is None or course is None:
            return
        east, north = enu_velocity(speed, course)
        message = TwistStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self._velocity_frame_id
        message.twist.linear.x = east
        message.twist.linear.y = north
        self._velocity_pub.publish(message)
        self._course_pub.publish(Float64(data=course))

    def _publish_diagnostics(self) -> None:
        now = time.monotonic()
        sentence_age = _age(now, self._last_sentence_time)
        fix_age = _age(now, self._last_fix_time)

        if self._serial is None:
            level = DiagnosticStatus.ERROR
            summary = 'serial port disconnected'
        elif sentence_age is None or sentence_age > self._stale_timeout:
            level = DiagnosticStatus.ERROR
            summary = 'GNSS data stale or absent'
        elif not self._state.has_fix:
            level = DiagnosticStatus.WARN
            summary = 'receiver connected; waiting for GNSS fix'
        else:
            level = DiagnosticStatus.OK
            summary = 'GNSS fix valid'

        status = DiagnosticStatus()
        status.level = level
        status.name = f'{self.get_namespace()}/neo_m9n_gps'.replace('//', '/')
        status.hardware_id = 'u-blox NEO-M9N-00B'
        status.message = summary
        status.values = [
            _key_value('requested_port', self._requested_port),
            _key_value('resolved_port', self._resolved_port or 'none'),
            _key_value('baud', self._baud),
            _key_value('fix_valid', self._state.has_fix),
            _key_value('fix_quality', self._state.fix_quality),
            _key_value('satellites', self._state.satellites),
            _key_value('hdop', self._state.hdop),
            _key_value('vdop', self._state.vdop),
            _key_value('sentence_age_sec', sentence_age),
            _key_value('fix_age_sec', fix_age),
            _key_value('valid_sentences', self._valid_sentences),
            _key_value('checksum_errors', self._checksum_errors),
            _key_value('parse_errors', self._parse_errors),
            _key_value('serial_errors', self._serial_errors),
            _key_value('receiver_text', self._state.receiver_text or 'none'),
            _key_value('last_error', self._last_error or 'none'),
        ]
        array = DiagnosticArray()
        array.header.stamp = self.get_clock().now().to_msg()
        array.status = [status]
        self._diagnostics_pub.publish(array)


def _nan_if_none(value: Optional[float]) -> float:
    return math.nan if value is None else value


def _age(now: float, timestamp: Optional[float]) -> Optional[float]:
    return None if timestamp is None else max(now - timestamp, 0.0)


def _key_value(key: str, value: object) -> KeyValue:
    if isinstance(value, float):
        text = f'{value:.3f}'
    elif value is None:
        text = 'unknown'
    else:
        text = str(value)
    return KeyValue(key=key, value=text)


def main(args: Optional[list[str]] = None) -> None:
    """Run the NEO-M9N node."""
    rclpy.init(args=args)
    node = NeoM9nGpsNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
