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

Run preflight before setup ends:

```bash
export WAYPOINT_FILE=/home/spearua/circ_waypoints.csv
export GPS_PORT=/dev/ttyTHS1
./scripts/competition_preflight.sh
```

## 3. Start the rover

```bash
ros2 launch spear_bringup rover.launch.py \
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

## 4. Start the base station

```bash
ros2 launch spear_bringup base_station.launch.py
```

The focused GPS panel shows fix health, gate order, distance, bearing,
approach heading, recording state, and capture controls. The larger legacy GUI
is excluded by default because its data feeds are still demonstrations.

## 5. Arm control

- Verify controller indexes using `ros2 topic echo /joy` before enabling power.
- The default deadman is button index 6.
- Motion is permitted only while the deadman is held.
- Releasing it or losing Joy messages for 0.30 seconds commands a stop.
- Begin at the lowest sensitivity and test every joint clear of people.
- Confirm the physical rover kill switch and independent remote motion stop;
  software stopping does not replace either control.

## 6. GPS operations

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

## 7. Required field validation

Do not freeze the release until two consecutive runs pass:

1. Cold boot and warm boot without editing source files.
2. Valid outdoor GPS fix with motors, EtherCAT, cameras, and radio active.
3. Seven mock gates loaded and advanced manually in order.
4. Three stationary sites captured more than 10 m apart.
5. Route PNG generated offline from the recorded session.
6. Joystick release and radio/Joy loss stop the arm within the measured limit.
7. GPS failure and camera packet loss are visible to the operator.
8. One hour on onboard power, followed by teardown within 10 minutes.
9. Physical kill switch test and current safety documentation verified.

Record the tested commit hash, JetPack version, ROS domain, radio settings,
camera bitrate, GPS port, and operator names. Tag only that validated commit.
