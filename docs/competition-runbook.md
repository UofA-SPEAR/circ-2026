# CIRC 2026 competition runbook

## 1. Clean build on each machine

```bash
cd ~/circ-2026
source /opt/ros/humble/setup.bash
rosdep install --from-paths . --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Use the same `ROS_DOMAIN_ID` on the Jetson and base station. Verify discovery
over the rover radio with external internet disconnected.

## 2. Prepare task waypoints

Copy `ultimate_gps_ros2/config/waypoints_template.csv` to a writable location.
Enter decimal-degree WGS-84 values in gate order:

```csv
name,latitude,longitude,approach_heading_deg
gate_1,51.1234567,-112.1234567,90
gate_2,51.1235567,-112.1233567,180
```

Run rover preflight on the Jetson before setup ends. It intentionally fails
while the drivetrain configuration still contains the checked-in placeholder
geometry, ratios, encoder counts, or steering limits:

```bash
export WAYPOINT_FILE=/home/spearua/circ_waypoints.csv
export GPS_PORT=/dev/ttyTHS1
PREFLIGHT_ROLE=rover ./scripts/competition_preflight.sh
```

Run the base-station checks on the operator computer with both controllers
connected:

```bash
export ARM_GAMEPAD_DEVICE_ID=0
export DRIVE_GAMEPAD_DEVICE_ID=1
PREFLIGHT_ROLE=base_station ./scripts/competition_preflight.sh
```

## 3. Start the rover

```bash
ros2 launch spear_bringup rover.launch.py \
  drive_profile:=crawl \
  receiver_ip:=192.168.8.224 \
  waypoint_file:="$WAYPOINT_FILE"
```

The GPS recorder starts automatically and writes under
`~/.ros/spear_gps_sessions`. The camera default is 1.5 Mbit/s per enabled
stream. Disable an unused stream at runtime to protect radio capacity:

```bash
ros2 topic pub --once /camera_settings std_msgs/msg/String \
  "data: '5007,enabled=0'"
```

The launch records diagnostics, commands, odometry, joint state, TF, IMU/GPS
inputs, and operator-control state under `~/.ros/spear_bags`. Camera video is
excluded. Recording stops after two hours or 10 GiB by default. Override the
limits explicitly when required:

```bash
ros2 launch spear_bringup rover.launch.py \
  bag_max_duration_sec:=3600 bag_max_total_size_mb:=5120
```

The EtherCAT master starts when either the arm or drivetrain is requested.
Drive-only degraded operation therefore does not load MoveIt or arm motion
controllers:

```bash
ros2 launch spear_bringup rover.launch.py \
  use_arm:=false use_drive:=true drive_profile:=crawl
```

## 4. Start the base station

```bash
ros2 launch spear_bringup base_station.launch.py \
  gamepad_device_id:=0 \
  drive_gamepad_device_id:=1 \
  drive_profile:=crawl
```

The focused GPS panel shows fix health, gate order, distance, bearing,
approach heading, recording state, and capture controls. The larger legacy GUI
is excluded by default because its data feeds are still demonstrations.

The arm controller publishes `/joy`; the drive controller publishes
`/drive/joy`. Both cross the rover radio. Their safety adapters and 0.30 s
watchdogs run on the Jetson, so radio or base-station loss is handled locally.
Do not run another publisher on either topic: both adapters require exactly one
publisher before accepting motion.

## 5. Arm control

- The launch uses ROS `game_controller_node`, which normalizes supported Xbox,
  PlayStation, and similar controllers to SDL's standard layout.
- Run `ros2 run joy joy_enumerate_devices` and select another controller with
  `gamepad_device_id:=N` if device 0 is not the arm controller.
- The default deadman is START/OPTIONS (standard button index 6).
- After startup or reconnect, release START/OPTIONS once. Center both sticks,
  release the shoulders/triggers, and hold START/OPTIONS for at least 0.15 s.
- Motion is permitted only while the deadman remains held. A held stick cannot
  arm the system; the status topic reports `neutral_required`.
- Releasing the deadman or losing Joy messages for 0.30 seconds commands a
  stop. After a timeout, another observed deadman release is mandatory.
- Change mode with Y/TRIANGLE and sensitivity with A/CROSS or D-pad up/down
  only while the deadman is released. Status is published as JSON on
  `/arm/teleop/status`.
- Begin at the lowest sensitivity and test every joint clear of people.
- Confirm the physical rover kill switch and independent remote motion stop;
  software stopping does not replace either control.

Standard motion mapping:

| Control | Joint mode | Cartesian mode |
| --- | --- | --- |
| Left stick X / Y | Joints 1 / 2 | Linear Y / X |
| Right stick X / Y | Joints 4 / 3 | Angular X / Y |
| Left / right trigger | Joint 6 differential | Linear Z differential |
| Left / right shoulder | Joint 5 differential | Angular Z differential |

Validate the complete controller mapping before enabling the arm hardware:

```bash
ros2 launch plex_moveit gamepad_check.launch.py gamepad_device_id:=0
```

This check launch publishes only to isolated `/arm/teleop_check/*` topics; it
does not feed MoveIt Servo. In another terminal, inspect the status and mapped
commands while testing the release, neutral, deadman, disconnect, mode, and
sensitivity behavior:

```bash
ros2 topic echo /arm/teleop_check/status
ros2 topic echo /arm/teleop_check/joint_commands
ros2 topic echo /arm/teleop_check/twist_commands
```

Use the complete measurable sign-off procedure in
[the arm joystick acceptance test](joystick-acceptance-test.md) before the
controller is approved for a competition run.

## 6. Drive control

- The drive controller defaults to SDL device `1` and the `crawl` profile.
- The right bumper is the held drive deadman; the left bumper enables precision
  scaling.
- After startup or reconnect, release the deadman once and hold both sticks
  neutral for 0.20 seconds before driving.
- Left-stick vertical commands forward/reverse. Right-stick horizontal commands
  curvature/yaw. Point turns are disabled.
- Releasing the deadman, losing Joy, losing the radio, or losing the command
  stream commands zero current locally on the rover.
- Physically straighten the four steering wheels before controller activation;
  their relative encoders are captured as zero on activation.
- Begin every new hardware configuration in `crawl`. Use `wet` only after field
  tuning and `normal` only after the rover passes the complete acceptance run.

Confirm the isolated topics and active rover controller after launch:

```bash
ros2 topic info /joy --verbose
ros2 topic info /drive/joy --verbose
ros2 control list_controllers -c /controller_manager
ros2 topic echo --once /spear_drive_controller/diagnostics
```

Both Joy topics must report exactly one publisher. `joint_state_broadcaster`,
`velocity_controller`, `control_word_controller`, and
`spear_drive_controller` must be active for full arm-and-drive operation.

## 7. GPS operations

The panel invokes these services; terminal equivalents are available:

```bash
ros2 param set /gps_mission waypoints_file /home/spearua/circ_waypoints.csv
ros2 service call /gps/mission/reload_waypoints std_srvs/srv/Trigger '{}'
ros2 service call /gps/mission/next_waypoint std_srvs/srv/Trigger '{}'
ros2 service call /gps/mission/previous_waypoint std_srvs/srv/Trigger '{}'
ros2 service call /gps/mission/capture_site std_srvs/srv/Trigger '{}'
ros2 service call /gps/mission/capture_landmark std_srvs/srv/Trigger '{}'
ros2 service call /gps/mission/stop_recording std_srvs/srv/Trigger '{}'
```

Site capture requires approximately 10 seconds of valid stationary fixes and
records sample count, spread, satellites, HDOP, and accuracy. A warning is
returned when a site is less than 10 m from another captured site.

Generate an offline report image after stopping the session:

```bash
ros2 run ultimate_gps_ros2 gps_route_map \
  ~/.ros/spear_gps_sessions/SESSION_DIRECTORY \
  --output ~/route_map.png
```

Each session contains `track.csv`, `markers.csv`, `raw_nmea.log`, and
`route.geojson`. Copy the complete directory before teardown.

## 8. Required field validation

Do not freeze the release until two consecutive runs pass:

1. Cold boot and warm boot without editing source files.
2. Valid outdoor GPS fix with motors, EtherCAT, cameras, and radio active.
3. Seven mock gates loaded and advanced manually in order.
4. Three stationary sites captured more than 10 m apart.
5. Route PNG generated offline from the recorded session.
6. Arm and drive Joy topics each have exactly one publisher.
7. Deadman release and radio/Joy loss stop both arm and drive within the
   measured limits.
8. Each drive and steering actuator passes the lifted-rover direction and
   encoder-sign check at crawl limits.
9. GPS failure, drivetrain degradation, and camera packet loss are visible to
   the operator.
10. The bounded rosbag opens with `ros2 bag info` and contains commands,
    odometry, joint state, GPS, and diagnostics.
11. One hour on onboard power, followed by teardown within 10 minutes.
12. Physical kill switch test and current safety documentation verified.

Record the tested commit hash, JetPack version, ROS domain, radio settings,
camera bitrate, GPS port, and operator names. Tag only that validated commit.
