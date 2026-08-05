# Adafruit Ultimate GPS Breakout V3 ROS 2 driver

`ultimate_gps_ros2` connects the Adafruit Ultimate GPS Breakout V3 (MTK3339)
to ROS 2 through its TTL UART NMEA interface. It is intended for ROS 2 Humble
and the CIRC 2026 rover workspace.

## ROS interfaces

| Interface | Type | Purpose |
| --- | --- | --- |
| `/gps/fix` | `sensor_msgs/msg/NavSatFix` | WGS-84 position and fix status |
| `/gps/velocity` | `geometry_msgs/msg/TwistStamped` | East/north ground velocity from RMC |
| `/gps/nmea` | `std_msgs/msg/String` | Raw NMEA/PMTK sentences |
| `/gps/time_reference` | `sensor_msgs/msg/TimeReference` | UTC time from RMC |
| `/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | Serial, fix, stream, and configuration health |
| `/gps/reconfigure` | `std_srvs/srv/Trigger` | Resend receiver output/rate commands |
| `/gps/mission/status` | `std_msgs/msg/String` | JSON fix, recording, waypoint, distance, and bearing state |

The node validates NMEA checksums, accepts talker IDs such as `GP` and `GN`,
publishes an explicit no-fix state, rate-limits repeated errors, and reconnects
when the serial adapter is unplugged and restored.

The Jetson competition launch also starts `gps_mission_node`. It records valid
fixes and raw NMEA onboard, loads ordered gate waypoints from CSV, calculates
distance/bearing, captures averaged field sites, and updates GeoJSON atomically.
See `docs/competition-runbook.md` at the workspace root for the operator flow.

## Wiring

The breakout uses TTL UART. Do **not** connect it to an RS-232 port.

| Ultimate GPS V3 | USB-to-TTL adapter or onboard UART |
| --- | --- |
| `VIN` | A supported 3.0–5.5 V supply |
| `GND` | Ground |
| `TX` | Host `RX` |
| `RX` | Host `TX` |

The GPS `TX` output uses 3.3 V logic. The breakout `RX` input accepts 3.3 V or
5 V logic. Connecting `RX` is required when `configure_receiver` is `true`.
Mount the patch antenna facing the sky and away from motor wiring, metal
obstruction, high-current electronics, and radio transmitters.

### Jetson AGX Orin Developer Kit direct-header wiring

For the NVIDIA AGX Orin Developer Kit carrier board, power the Jetson off
before connecting or moving wires. Use physical pin numbers on the J30 40-pin
header, counting from the white pin-1 triangle:

| Ultimate GPS V3 | Jetson J30 physical pin |
| --- | --- |
| `VIN` | Pin 2: 5 V |
| `GND` | Pin 6: ground |
| `TX` | Pin 10: UART receive |
| `RX` | Pin 8: UART transmit |

The data wires are crossed: GPS transmit goes to Jetson receive, and GPS
receive goes to Jetson transmit. The J30 UART signals and GPS TX are 3.3 V
logic. Do not connect 5 V directly to either UART signal pin.

On the Jetson, first identify the available Tegra UART:

```bash
ls -l /dev/ttyTHS*
sudo dmesg | grep -E 'ttyTHS|serial'
```

J30 pins 8/10 are normally `/dev/ttyTHS1` on the AGX Orin Developer Kit. If
the device is absent, use NVIDIA Jetson-IO to enable the UART on the 40-pin
header and reboot. Do not disable a serial-getty blindly; first check whether
one is actually using the port:

```bash
systemctl status serial-getty@ttyTHS1.service
```

The package includes `config/jetson_agx_orin.yaml` and a dedicated launch file:

```bash
ros2 launch ultimate_gps_ros2 gps_jetson_agx_orin.launch.py
```

## Test the hardware before ROS

Install pyserial and find the port:

```bash
sudo apt install python3-serial
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

After building and sourcing the package, run the passive probe outdoors:

```bash
ros2 run ultimate_gps_ros2 gps_serial_probe \
  --port /dev/ttyUSB0 --duration 60
```

NMEA data without a valid position means the serial connection works but the
receiver still needs a clear view of the sky. A cold start can take a minute or
more in real conditions.

## Build

From the repository root:

```bash
source /opt/ros/humble/setup.bash
rosdep install --from-paths ultimate_gps_ros2 --ignore-src -r -y
colcon build --symlink-install --packages-select ultimate_gps_ros2
source install/setup.bash
```

## Run

Use the default `/dev/ttyUSB0` port:

```bash
ros2 launch ultimate_gps_ros2 gps.launch.py
```

Override the port or disable receiver writes for a TX-only connection:

```bash
ros2 launch ultimate_gps_ros2 gps.launch.py \
  port:=/dev/ttyACM0 configure_receiver:=false
```

Inspect the data and diagnostics:

```bash
ros2 topic echo /gps/fix
ros2 topic echo /diagnostics
ros2 topic hz /gps/fix
```

The default configuration requests only RMC and GGA at 5 Hz. Adafruit notes
that this combination fits at 9600 baud; outputting every NMEA sentence at high
rates does not.

## Stable device name

Competition software should not depend on whether Linux happens to assign
`ttyUSB0` or `ttyUSB1`. Inspect the adapter:

```bash
udevadm info --attribute-walk --name=/dev/ttyUSB0
```

Copy `udev/99-spear-gps.rules.example` to
`/etc/udev/rules.d/99-spear-gps.rules`, replace its placeholders, reload udev,
and change `config/gps.yaml` to `/dev/spear_gps`. The adapter should have a
unique serial number; rules using only vendor/product IDs can match unrelated
devices.

The ROS user normally needs access through the `dialout` group:

```bash
sudo usermod -aG dialout "$USER"
```

Log out and back in after changing group membership.

## Parameters

| Parameter | Default | Notes |
| --- | --- | --- |
| `port` | `/dev/ttyUSB0` | Serial device or stable udev symlink |
| `baud_rate` | `9600` | Ultimate GPS factory/default baud rate |
| `frame_id` | `gps_link` | Frame of the antenna position |
| `velocity_frame_id` | `map` | ENU axes for converted RMC velocity |
| `configure_receiver` | `true` | Send PMTK output/rate commands on connect |
| `update_rate_hz` | `5` | Supported RMC+GGA values: 1, 2, or 5 |
| `reconnect_delay_sec` | `2.0` | Delay between serial open attempts |
| `stale_after_sec` | `2.0` | Diagnostic threshold for missing GGA |
| `uere_m` | `3.0` | Converts HDOP to approximate covariance |
| `diagnostics_rate_hz` | `1.0` | Diagnostic publication frequency |

## Physical fix indication

The breakout's red FIX LED normally blinks about once per second while
searching. After acquiring a position fix it blinks much less frequently. Use
ROS diagnostics as the operational source of truth because it also detects
serial disconnects, stale data, checksum problems, and receiver configuration
failures.
