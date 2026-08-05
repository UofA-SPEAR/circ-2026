# Arm joystick acceptance test

Run this test against the exact commit, controller, base-station computer,
Jetson image, radio configuration, and arm hardware intended for competition.
Record evidence for both the cold-start run and a second run after reboot.

## Acceptance limits

- No nonzero command before an observed deadman release and 0.15 s neutral
  hold.
- Deadman release produces a zero command within 0.10 s.
- Joy stream, controller, base-station, or radio loss produces a zero command
  within 0.40 s (the software threshold is 0.30 s).
- Reconnect never resumes motion until another deadman release and neutral arm.
- Zero or multiple `/joy` publishers keep the arm locked.
- Every commanded joint and Cartesian direction agrees with the signed mapping.
- No test causes a joint-limit, collision, or singularity hard-stop fault.

## A. Unpowered controller check

Leave arm drive power disabled and keep the physical emergency stop engaged.
On the computer where the controller is plugged in:

```bash
source /opt/ros/humble/setup.bash
source ~/circ-2026/install/setup.bash
ros2 run joy joy_enumerate_devices
ros2 launch plex_moveit gamepad_check.launch.py gamepad_device_id:=0
```

In separate terminals:

```bash
ros2 topic echo /arm/teleop_check/status
ros2 topic echo /arm/teleop_check/joint_commands
ros2 topic echo /arm/teleop_check/twist_commands
```

| Test | Expected result | Pass |
| --- | --- | --- |
| Start while holding deadman | `release_required`; commands remain zero | ☐ |
| Release deadman | `deadman_released` | ☐ |
| Hold a stick, then deadman | `neutral_required`; commands remain zero | ☐ |
| Center controls and hold deadman | `neutral_hold`, then `armed` after 0.15 s | ☐ |
| Release deadman while commanding | Zero command within 0.10 s | ☐ |
| Unplug and reconnect controller | `controller_timeout`; requires release again | ☐ |
| Y/TRIANGLE while disarmed | Joint/Cartesian mode toggles once | ☐ |
| A/CROSS and D-pad while disarmed | Sensitivity changes one step per press | ☐ |
| Settings buttons while armed | Mode and sensitivity do not change | ☐ |
| Start a second `/joy` publisher | `joy_publisher_count_invalid`; stays locked | ☐ |

Stop the check launch before running the competition base-station launch.

## B. Base-station-to-Jetson radio check

Use the same nonzero `ROS_DOMAIN_ID` on both computers and ensure
`ROS_LOCALHOST_ONLY` is unset or `0`. Start the rover arm stack with drive power
still disabled, then start the base station. On the Jetson:

```bash
ros2 topic hz /joy
ros2 topic echo /arm/teleop/status
ros2 topic info /joy --verbose
```

| Test | Expected result | Pass |
| --- | --- | --- |
| Normal link | Approximately 30 Hz and exactly one publisher | ☐ |
| Stop base-station launch | Jetson reports timeout within 0.40 s | ☐ |
| Restart base-station launch | Arm remains locked until deadman release | ☐ |
| Disconnect the rover radio | Zero command within 0.40 s | ☐ |
| Restore the rover radio | No automatic re-arm or motion | ☐ |

## C. Powered low-speed direction check

Clear the arm workspace, assign one emergency-stop operator, support any load,
and begin at sensitivity `0.0125`. Exercise one control at a time with short
pulses. Stop immediately if the observed direction differs from the table.

| Control | Expected joint motion | Expected Cartesian motion | Pass |
| --- | --- | --- | --- |
| Left stick X | Joint 1 | Linear Y | ☐ |
| Left stick Y | Joint 2 | Linear X | ☐ |
| Right stick X | Joint 4 | Angular X | ☐ |
| Right stick Y | Joint 3 | Angular Y | ☐ |
| Trigger differential | Joint 6 | Linear Z | ☐ |
| Shoulder differential | Joint 5 | Angular Z | ☐ |

Repeat deadman release, controller disconnect, and radio-loss tests while
commanding the lowest practical speed. Measure video frame timestamps or an
equivalent monotonic trace; do not accept a subjective “looks fast enough.”

## Test record

| Field | Recorded value |
| --- | --- |
| Git commit | |
| Date / operators | |
| Controller make, model, USB/Bluetooth | |
| Base-station OS and ROS | |
| JetPack and ROS | |
| `ROS_DOMAIN_ID` and RMW implementation | |
| Deadman-release worst case | |
| Radio-loss worst case | |
| Cold-start run | PASS / FAIL |
| Post-reboot run | PASS / FAIL |
| Deviations / corrective commits | |
