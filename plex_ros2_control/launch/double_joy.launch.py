#!/usr/bin/env python3
"""
Launch two joystick drivers on the same machine, using only the `joy` package
that ships with ros-<distro>-desktop.

    arm controller    ->  /joy_arm
    drive controller  ->  /joy_drive

Device ordering
---------------
joy_node (SDL backend) picks its device one of two ways:

    device_name : the SDL name string. Stable across reboots and replugs, but
                  only unambiguous if the two controllers report DIFFERENT
                  names. This is the option you want.
    device_id   : the SDL enumeration index (0, 1, ...). Assigned in plug order,
                  so it swaps on you. Only a last resort -- see the bottom of
                  this file.

device_name takes precedence when it is non-empty.

List the names of everything currently plugged in with:

    ros2 run joy joy_enumerate_devices

and paste the exact strings into the constants below. Matching is on the full
name, so copy it verbatim, spaces and all.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# ---- EDIT THESE to match `ros2 run joy joy_enumerate_devices` ----------------
ARM_NAME_DEFAULT = 'Xbox Series X Controller'
DRIVE_NAME_DEFAULT = 'OpenTX Radiomaster TX16S Joystick'
# -----------------------------------------------------------------------------


def generate_launch_description():
    arm_name = LaunchConfiguration('arm_device_name')
    drive_name = LaunchConfiguration('drive_device_name')
    deadzone = LaunchConfiguration('deadzone')
    autorepeat_rate = LaunchConfiguration('autorepeat_rate')

    args = [
        DeclareLaunchArgument(
            'arm_device_name',
            default_value=ARM_NAME_DEFAULT,
            description='SDL device name of the arm controller.'),
        DeclareLaunchArgument(
            'drive_device_name',
            default_value=DRIVE_NAME_DEFAULT,
            description='SDL device name of the drive controller.'),
        DeclareLaunchArgument(
            'deadzone',
            default_value='0.05',
            description='Axis deadzone, as a fraction of full scale.'),
        DeclareLaunchArgument(
            'autorepeat_rate',
            default_value='20.0',
            description='Hz at which the last state is republished. 0 disables.'),
    ]

    common_params = {
        'deadzone': deadzone,
        'autorepeat_rate': autorepeat_rate,
        'sticky_buttons': False,
        'coalesce_interval_ms': 1,
    }

    arm_joy = Node(
        package='joy',
        executable='joy_node',
        name='joy_arm',
        output='screen',
        parameters=[{**common_params, 'device_name': arm_name}],
        remappings=[
            ('/joy', '/joy_arm'),
            ('/joy/set_feedback', '/joy_arm/set_feedback'),
        ],
    )

    drive_joy = Node(
        package='joy',
        executable='joy_node',
        name='joy_drive',
        output='screen',
        parameters=[{**common_params, 'device_name': drive_name}],
        remappings=[
            ('/joy', '/joy_drive'),
            ('/joy/set_feedback', '/joy_drive/set_feedback'),
        ],
    )

    return LaunchDescription(args + [arm_joy, drive_joy])


# -----------------------------------------------------------------------------
# If both controllers are the same model
#
# They report the same SDL name, so device_name cannot separate them and you are
# left with device_id, which follows plug order. Two ways out, both desktop-only:
#
# 1. Plug order discipline. Set 'device_id': 0 on the arm node and 1 on the
#    drive node, and always power up / plug in the arm controller first. Fragile
#    but needs nothing installed.
#
# 2. Rename one of them in udev, then keep using device_name above. SDL reads the
#    name from the device, and udev can override it. In
#    /etc/udev/rules.d/99-joysticks.rules, keyed on the physical USB port:
#
#      SUBSYSTEM=="input", KERNELS=="1-2", ENV{ID_INPUT_JOYSTICK}=="1", \
#          ATTRS{name}!="", ENV{NAME}="ArmPad"
#
#    Get the KERNELS value from `udevadm info -a -n /dev/input/js0 | grep KERNELS`,
#    reload with `sudo udevadm control --reload-rules && sudo udevadm trigger`,
#    replug, and re-run joy_enumerate_devices to confirm the new name appears.
#
# Note on older distros: joy_node used 'coalesce_interval' (seconds, double)
# before the SDL rewrite, not 'coalesce_interval_ms'. If launch complains about
# an unknown parameter, that is the one to swap.
# -----------------------------------------------------------------------------