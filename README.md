# SPEAR CIRC 2026 rover workspace

This ROS 2 Humble workspace contains the PLEX arm, EtherCAT control, rover
cameras, operator interfaces, and the Adafruit Ultimate GPS subsystem.

The competition entry points are:

```bash
# Jetson AGX Orin
ros2 launch spear_bringup rover.launch.py \
  receiver_ip:=192.168.8.224 \
  waypoint_file:=/home/spearua/circ_waypoints.csv

# Base station
ros2 launch spear_bringup base_station.launch.py
```

Build, deployment, task setup, fail-safe checks, and field validation are
documented in [the competition runbook](docs/competition-runbook.md).

The main GUI remains optional in the competition launch. The focused GPS
mission panel and camera application are the default operator interfaces.
