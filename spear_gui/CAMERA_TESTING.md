# Eight-camera Jetson test

This branch runs each camera in its own ROS process. Camera startup is
serialized until a real encoded RTP buffer is observed, and a crashed sender
process is respawned by ROS launch.

## Before every connection-layout test

GMSL2 cameras should be connected before boot. After connecting, disconnecting,
or moving a camera, restart the ZED daemon before launching the senders:

```bash
sudo systemctl restart zed_x_daemon
sudo dmesg | grep zedx
```

Confirm that the ZED SDK lists all eight expected serial numbers. If it lists
only seven, fix the camera, cable, capture-card port, power, or ZED driver before
testing ROS.

## Build and run

```bash
cd ~/circ-2026
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select spear_gui
source install/setup.bash
ros2 launch spear_gui camera_senders.launch.py receiver_ip:=192.168.10.11
```

Replace `192.168.10.11` with the receiver computer's rover-network address.

Each camera should print these messages, in order:

```text
PLAYING requested; waiting for the first encoded buffer
first encoded buffer received; streaming to <receiver>:<port>
```

Status for all workers is multiplexed onto `/status` and includes the serial
number and UDP port:

```bash
ros2 topic echo /status
```

A healthy test must show `streaming` for eight unique serial numbers and ports
5000 through 5007. `opening` means that worker is waiting for the startup gate
or its first frame. `retrying` means the camera or encoding pipeline failed.

## Identify the failing boundary

If only seven streams appear, reverse the order of `CAMERAS` in
`launch/camera_senders.launch.py` for one diagnostic run:

- A different missing serial indicates startup or encoder resource pressure.
- The same missing serial indicates a camera, cable, configuration, or serial
  number problem.
- The same physical GMSL2 port failing after swapping cameras indicates a
  capture-card group, connector, or power problem.
- Eight `streaming` statuses with only seven receiver images indicates a UDP,
  decoder, or GUI problem on the receiver.

The full launch uses HD1200 at 30 FPS and the left image from each stereo
camera. These values are intentionally explicit so plugin defaults cannot vary
between installed ZED SDK releases.
