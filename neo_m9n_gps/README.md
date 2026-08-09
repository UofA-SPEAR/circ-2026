# neo_m9n_gps

ROS 2 Humble serial driver for the u-blox NEO-M9N-00B GNSS receiver. It works
with the receiver's factory NMEA output and publishes standard ROS messages.

## ROS interface

All relative topics are placed below the launch namespace, which defaults to
`/gps`.

| Topic | Type | Meaning |
|---|---|---|
| `fix` | `sensor_msgs/msg/NavSatFix` | WGS84 latitude, longitude and ellipsoid altitude |
| `velocity` | `geometry_msgs/msg/TwistStamped` | ENU velocity: x=east, y=north |
| `course_deg` | `std_msgs/msg/Float64` | Course over ground, clockwise from true north |
| `satellites` | `std_msgs/msg/UInt32` | Satellites used/reported by GGA |
| `raw` | `std_msgs/msg/String` | Raw NMEA lines when `publish_raw` is true |
| `/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | Connection, fix, stale-data and parser health |

The node has no subscribed ROS topics, services, or actions. See the complete
[topic and interface reference](docs/ROS_INTERFACES.md) for publication
conditions, units, frames, QoS and no-fix behaviour.

GGA reports altitude above mean sea level. `NavSatFix` requires altitude above
the WGS84 ellipsoid, so the driver adds the GGA geoid separation when present.
Position covariance is an approximation derived from DOP and configurable UERE.

## Build

```bash
sudo apt install python3-serial
cd ~/circ-2026
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select neo_m9n_gps
source install/setup.bash
```

The serial user must be able to access the device. On Ubuntu this normally
means membership in `dialout`; log out and back in after changing groups.

```bash
sudo usermod -aG dialout "$USER"
```

## Find and run the receiver

For a USB carrier or USB-to-UART adapter:

```bash
ros2 run neo_m9n_gps gps_probe
ros2 launch neo_m9n_gps neo_m9n.launch.py port:=auto
```

For a Jetson GPIO UART, first verify the Linux device belonging to the selected
carrier-board pins, then pass it explicitly:

```bash
ros2 launch neo_m9n_gps neo_m9n.launch.py port:=/dev/ttyTHS0
```

The NEO-M9N factory UART rate is 38,400 baud. Override it only if the receiver
has previously been reconfigured:

```bash
ros2 launch neo_m9n_gps neo_m9n.launch.py \
  port:=/dev/ttyTHS0 baud:=115200
```

Check output:

```bash
ros2 topic echo /gps/fix
ros2 topic echo /gps/satellites
ros2 topic echo /diagnostics
```

Test outdoors with the antenna facing the sky. A connected receiver without a
position is reported as `WARN`; missing or stale serial data is `ERROR`.

## UART electrical warning

If this is a **bare NEO-M9N module**, it is not a 5 V breakout: its documented
VCC range is 2.7-3.6 V. Connect module TX to Jetson RX, module RX to Jetson TX,
and share ground, using the voltage and antenna circuitry required by the
actual carrier board. Do not assume a board labelled `VIN` has a regulator or
level shifter—check that board's schematic first.

See [docs/NEO_M9N_REFERENCES.md](docs/NEO_M9N_REFERENCES.md) for the official
u-blox documentation used by this driver.
