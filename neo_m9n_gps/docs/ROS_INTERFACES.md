# ROS interfaces

Launching `neo_m9n.launch.py` uses the `/gps` namespace by default. Relative
topic names therefore appear with the fully qualified names shown below. The
namespace can be changed with the `namespace` launch argument, and normal ROS
remapping can rename individual topics.

## Published topics

| Default topic | Message type | Rate / publication trigger | Contents |
|---|---|---|---|
| `/gps/fix` | `sensor_msgs/msg/NavSatFix` | Each checksum-valid NMEA GGA sentence; factory default is 1 Hz | WGS84 latitude/longitude, ellipsoid altitude, fix status, service mask and DOP-derived position covariance |
| `/gps/velocity` | `geometry_msgs/msg/TwistStamped` | Each valid RMC or usable VTG sentence | ENU ground velocity in m/s: `linear.x` is east, `linear.y` is north and `linear.z` is zero |
| `/gps/course_deg` | `std_msgs/msg/Float64` | Published with `/gps/velocity` | Course over ground in degrees, clockwise from true north in the range `[0, 360)` |
| `/gps/satellites` | `std_msgs/msg/UInt32` | Published with `/gps/fix` | Number of satellites reported in the latest GGA sentence |
| `/gps/raw` | `std_msgs/msg/String` | Every complete serial line when `publish_raw:=true` | Unmodified NMEA text without the serial CR/LF terminator; includes lines later rejected by checksum/parser validation |
| `/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | Periodic; 1 Hz by default | Serial connection, stale-data state, fix state, DOP, satellite count, parser counters and receiver TXT status |

`/diagnostics` is an absolute, system-wide topic and is not placed below the
GPS namespace. The other five topics are relative to the node namespace.

## Fix behaviour

- A valid GGA fix uses `NavSatStatus.STATUS_FIX`.
- A GGA sentence reporting no fix still produces `/gps/fix`, with
  `STATUS_NO_FIX`, non-existent coordinates represented as `NaN`, and unknown
  covariance. Consumers must check `message.status.status` before using it.
- NMEA GGA altitude is above mean sea level. The node adds geoid separation to
  publish the WGS84 ellipsoid altitude required by `NavSatFix`.
- Covariance is an approximation calculated from HDOP/VDOP and the configured
  user-equivalent range error (`uere_m`). It is not a receiver-reported UBX
  accuracy estimate.

## Frames and units

| Interface | Default frame | Units / convention |
|---|---|---|
| `/gps/fix` | `gps_link` | Latitude/longitude in decimal degrees; altitude in metres above WGS84 ellipsoid |
| `/gps/velocity` | `map` | ENU metres per second |
| `/gps/course_deg` | No header | Degrees clockwise from true north |

`frame_id` and `velocity_frame_id` are configurable parameters. The package
does not publish TF; the rover description must provide the transform to
`gps_link`.

## QoS

The standard publishers use reliable, volatile `KEEP_LAST` queues. Queue depth
is 10 for fixes, velocity, course, satellite count and diagnostics. Raw NMEA
uses depth 20.

## Inputs, services and actions

The driver has **no subscribed ROS topics, services, or actions**. Receiver
input comes directly from the configured serial device. Receiver configuration
is supplied as ROS parameters at startup.

## Inspect the live interface

```bash
ros2 node info /gps/neo_m9n_gps
ros2 topic list -t | grep -E '^/gps/|^/diagnostics'
ros2 topic echo /gps/fix
ros2 topic hz /gps/fix
```
