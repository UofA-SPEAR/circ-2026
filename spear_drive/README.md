# SPEAR drivetrain control

`spear_drive` is a self-contained ROS 2 package for the CIRC rover's six driven
wheels, four steering actuators, relative steering encoders, motor-side wheel
encoders, and optional IMU. It does not change or launch any existing arm,
EtherCAT, GPS, GUI, or bringup package.

## Implemented

- Four-wheel coordinated steering using parameterized wheel coordinates.
- Six independent motor-effort outputs with motor-side gear ratio, direction,
  wheel radius, speed, acceleration, deceleration, jerk, and effort limits.
- Steering-to-drive alignment gating to avoid loading the frame while the
  wheels are still turning.
- Per-wheel overspeed/slip effort reduction and IMU yaw feedback.
- Encoder odometry and drivetrain diagnostics.
- Command and IMU freshness checks local to the rover controller.
- Five-wheel and balanced four-wheel degraded modes when the hardware layer
  marks an individual motor velocity invalid while the EtherCAT slave stays online.
- A straight-only steering limp mode that isolates the drive motor behind a
  failed corner. An unknown or off-centre steering failure stops motion.
- An isolated drive joystick topic with release-before-arm, neutral hold,
  held deadman, precision mode, single-publisher check, and timeout.
- Mock hardware and dependency-free core tests.

This is the foundation for traction control, not a magic replacement for test
data. Collective wheel slip cannot be identified reliably from wheel encoders
alone. The IMU improves yaw control; a good terrain-speed estimate would improve
longitudinal slip estimation later.

Set `imu_topic` to the rover IMU's `sensor_msgs/Imu` topic. Once that stream is
verified, set `monitor_imu: true`; losing it will then select a reduced-speed
`IMU_DEGRADED` mode rather than stopping the rover.

## No hidden actuation switch

There is no `allow_actuation` parameter or extra enable service. Loading and
activating `spear_drive_controller` is the software-enable step. Releasing the
drive joystick deadman publishes zero immediately, and a stale command also
forces zero effort in the controller.

The rover still needs its independent physical E-stop/kill system. Software
timeouts are not a substitute for hardware power removal.

## Required measurements

Replace every placeholder called out in
[`config/drive_controller.yaml`](config/drive_controller.yaml) before a driven
test:

1. `wheel_x` and `wheel_y`: each wheel contact centre relative to `base_link`.
2. Loaded `wheel_radius` for all six wheels.
3. `drive_gear_ratio`: positive motor revolutions per wheel revolution.
4. `steering_gear_ratio`, or `1.0` if embedded reports knuckle angle directly.
5. `drive_direction` and `steering_direction` signs.
6. Four steering hard-stop angles with a mechanical safety margin.
7. Steering offsets after the wheels are mechanically straight.
8. Actual allowable motor-shaft torque and velocity-loop gains.

Because steering encoders are relative, all four wheels must be physically
straight before controller activation. `auto_zero_on_activate` records that
position as zero. With the deadman released, zero can be captured again with:

```bash
ros2 service call /spear_drive_controller/zero_steering std_srvs/srv/Trigger '{}'
```

## EtherCAT contract

The arm already owns EtherCAT master `0` at slave positions `0` through `5`.
The proposed, explicit cable order for this package is:

| Position | Actuator |
|---:|---|
| 6–11 | front-left, front-right, middle-left, middle-right, rear-left, rear-right drive |
| 12–15 | front-left, front-right, rear-left, rear-right steering |

The full mapping is in [`config/actuator_map.yaml`](config/actuator_map.yaml).
EtherCAT slave `position` is physical bus order, so the actual cable order must
match it.

Only one `ethercat_driver/EthercatDriver` may own master `0`. The macro in
[`description/ros2_control/drive_interfaces.ros2_control.xacro`](description/ros2_control/drive_interfaces.ros2_control.xacro)
is intended to be called inside the existing arm `<ros2_control>` system. Do not
start a second master for the drivetrain.

The embedded team must still provide the two real slave YAML files. A PDO
(Process Data Object) is the fixed cyclic EtherCAT mapping between a command or
sensor value and bytes on the wire. We need, for each slave:

- vendor/product identity;
- RxPDO index, subindex, type, scale, and unit for command;
- TxPDO index, subindex, type, scale, and unit for encoder/fault feedback;
- byte order and signedness;
- embedded stale-command watchdog behavior.

For limp mode, a motor or encoder fault must not take the EtherCAT slave off the
bus. The embedded/hardware layer should keep exchanging PDOs and expose only the
failed actuator state as non-finite (or later expose a dedicated fault state).
A disconnected slave or lost EtherCAT master is a system-level stop because the
controller can no longer prove commands are reaching the remaining actuators.

The ROS-facing contract is motor effort in N·m and motor encoder velocity in
rad/s for drive, and relative motor position in radians for steering. If
embedded uses normalized torque or encoder counts, the hardware/PDO layer must
convert those values before exposing the ROS interfaces. If embedded already
converts steering to knuckle radians, set `steering_gear_ratio` to `1.0`.

After those interfaces have been added to the existing single EtherCAT system,
physically straighten the steering and load/activate this controller with:

```bash
ros2 launch spear_drive load_drive_controller.launch.py \
  controller_manager:=/controller_manager profile:=crawl
```

This loader never creates hardware or a second master; it only asks the existing
controller manager to claim the 10 interfaces and activate the controller.

## Build and core tests

On the Jetson's ROS 2 workspace:

```bash
cd ~/circ-2026
source /opt/ros/humble/setup.bash
rosdep install --from-paths . --ignore-src -r -y
colcon build --symlink-install --packages-select spear_drive
source install/setup.bash
colcon test --packages-select spear_drive --event-handlers console_direct+
colcon test-result --verbose
```

The core kinematics/fault tests can also be compiled without ROS:

```bash
c++ -std=c++17 -Wall -Wextra -Wpedantic \
  -Ispear_drive/include \
  spear_drive/src/drive_core.cpp spear_drive/src/fault_manager.cpp \
  spear_drive/test/test_drive_core.cpp -o /tmp/test_drive_core
/tmp/test_drive_core
```

## Mock run

The mock uses a separate fake 10-actuator system and never contacts EtherCAT:

```bash
ros2 launch spear_drive drive_mock.launch.py profile:=crawl
```

In a second terminal, confirm the controller and diagnostics:

```bash
source /opt/ros/humble/setup.bash
source ~/circ-2026/install/setup.bash
ros2 control list_controllers
ros2 topic echo /spear_drive_controller/diagnostics
ros2 topic pub --once /spear_drive_controller/cmd_vel \
  geometry_msgs/msg/TwistStamped \
  "{twist: {linear: {x: 0.1}, angular: {z: 0.1}}}"
```

The generic mock does not simulate rover mass, motor dynamics, or traction; it
validates ROS loading, interface claiming, steering commands, timeouts, and
diagnostics.

## Drive joystick

Start the drive gamepad separately from the arm gamepad:

```bash
ros2 launch spear_drive drive_teleop.launch.py device_id:=1 profile:=crawl
```

The existing base-station launch uses SDL device `0` for the arm; this launch
defaults drive to device `1` and publishes it only as `/drive/joy`.

The drive gamepad is the only publisher allowed on `/drive/joy`. Verify axis and
button numbers before enabling hardware:

```bash
ros2 topic echo /drive/joy
ros2 topic info /drive/joy --verbose
```

With ROS `game_controller_node` (SDL), the default mapping is left-stick
vertical axis `1`, right-stick horizontal axis `2`, right-bumper deadman button
`5`, and left-bumper precision button `4`.
Release the deadman once, hold both axes neutral for 0.2 seconds, then hold the
deadman to drive. Change the mapping in the YAML if the actual controllers
report different indexes.

The launch accepts `crawl`, `wet`, and `normal` profiles. Competition startup
should name a profile explicitly; begin all commissioning with `crawl`.

For two identical USB gamepads, create stable udev identities based on device
serial/USB path before competition. Do not rely only on whichever controller
happens to become `/dev/input/js0` after a reboot.

## Hardware commissioning order

1. Embedded bench test proves PDO units, scaling, directions, and watchdog.
2. With rover drive power isolated, verify all 10 encoder signs by hand.
3. Lift all wheels; activate, zero steering, and test one actuator at a time at
   crawl limits.
4. Verify E-stop and radio-loss behavior under commanded motion.
5. Low-speed flat-ground geometry and odometry tuning.
6. Tune velocity/effort limits with current and temperature feedback visible.
7. Test each single-wheel and steering feedback failure intentionally.
8. Tune the wet profile on representative wet soil, then lock the competition
   parameter files and record their commit.

Do not use the placeholder effort, geometry, ratio, or limit values for an
on-ground hardware test.
