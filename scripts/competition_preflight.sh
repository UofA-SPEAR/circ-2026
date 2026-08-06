#!/usr/bin/env bash
set -uo pipefail

failures=0
warnings=0
gps_port="${GPS_PORT:-/dev/ttyTHS1}"
waypoint_file="${WAYPOINT_FILE:-}"
expected_ethercat_slaves="${EXPECTED_ETHERCAT_SLAVES:-16}"
arm_gamepad_device_id="${ARM_GAMEPAD_DEVICE_ID:-0}"
drive_gamepad_device_id="${DRIVE_GAMEPAD_DEVICE_ID:-1}"
preflight_role="${PREFLIGHT_ROLE:-rover}"
script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
workspace_root=$(dirname "$script_directory")

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1"; warnings=$((warnings + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failures=$((failures + 1)); }

case "$preflight_role" in
  rover|base_station)
    pass "preflight role is $preflight_role"
    ;;
  *)
    fail "PREFLIGHT_ROLE must be rover or base_station"
    ;;
esac

if command -v ros2 >/dev/null 2>&1; then
  pass "ros2 is available"
else
  fail "ros2 is unavailable; source /opt/ros/humble/setup.bash"
fi

if [ "${ROS_LOCALHOST_ONLY:-0}" = "1" ]; then
  fail "ROS_LOCALHOST_ONLY=1 blocks base-station/rover communication"
else
  pass "ROS discovery is not restricted to localhost"
fi

if [ -n "${ROS_DOMAIN_ID:-}" ]; then
  pass "ROS_DOMAIN_ID is set to $ROS_DOMAIN_ID"
else
  warn "ROS_DOMAIN_ID is unset; explicitly configure the same value on both computers"
fi

if [ "$arm_gamepad_device_id" = "$drive_gamepad_device_id" ]; then
  fail "arm and drive gamepad device IDs must be different"
else
  pass "arm and drive gamepad device IDs are distinct"
fi

if [ "$preflight_role" = "base_station" ]; then
  gamepad_count=0
  for gamepad in /dev/input/js*; do
    if [ -e "$gamepad" ]; then
      gamepad_count=$((gamepad_count + 1))
    fi
  done
  if [ "$gamepad_count" -ge 2 ]; then
    pass "at least two Linux joystick devices are present"
  else
    fail "fewer than two /dev/input/js* devices are present"
  fi
fi

if [ "$preflight_role" = "rover" ]; then
  if [ -e "$gps_port" ]; then
    pass "GPS device exists at $gps_port"
    if [ -r "$gps_port" ] && [ -w "$gps_port" ]; then
      pass "GPS device is readable and writable"
    else
      fail "GPS permissions are insufficient for the current user"
    fi
  else
    fail "GPS device is missing at $gps_port"
  fi

  if id -nG | tr ' ' '\n' | grep -qx dialout; then
    pass "current user belongs to dialout"
  else
    warn "current user is not in dialout"
  fi
fi

available_kb=$(df -Pk . | awk 'NR==2 {print $4}')
if [ "${available_kb:-0}" -ge 5242880 ]; then
  pass "at least 5 GiB of workspace storage is free"
else
  warn "less than 5 GiB of workspace storage is free"
fi

if [ -n "$waypoint_file" ]; then
  if [ -f "$waypoint_file" ]; then
    rows=$(awk -F, \
      'NR > 1 && $1 !~ /^#/ && $1 != "" {count++} END {print count+0}' \
      "$waypoint_file")
    pass "waypoint file exists with $rows target(s)"
    if [ "$rows" -ne 7 ]; then
      warn "Refreshment Delivery normally requires exactly seven ordered gates"
    fi
  else
    fail "WAYPOINT_FILE does not exist: $waypoint_file"
  fi
else
  warn "WAYPOINT_FILE is unset; gate guidance will start without targets"
fi

for package in \
  controller_manager joy ros2bag ultimate_gps_ros2 spear_gui plex_moveit \
  plex_ethercat plex_ros2_control spear_drive spear_bringup; do
  if command -v ros2 >/dev/null 2>&1 && ros2 pkg prefix "$package" >/dev/null 2>&1; then
    pass "ROS package installed: $package"
  else
    fail "ROS package unavailable: $package"
  fi
done

if command -v ros2 >/dev/null 2>&1 \
  && ros2 pkg executables spear_bringup 2>/dev/null \
    | awk '$2 == "bounded_recorder" {found=1} END {exit !found}'; then
  pass "bounded competition recorder is installed"
else
  fail "bounded competition recorder is not installed; rebuild spear_bringup"
fi

if [ "$preflight_role" = "rover" ]; then
  if command -v ethercat >/dev/null 2>&1; then
    if ethercat_output=$(ethercat slaves 2>&1); then
      ethercat_count=$(printf '%s\n' "$ethercat_output" | awk 'NF {count++} END {print count+0}')
      if [ "$ethercat_count" -eq "$expected_ethercat_slaves" ]; then
        pass "EtherCAT reports all $expected_ethercat_slaves expected slaves"
      else
        fail "EtherCAT reports $ethercat_count slave(s); expected $expected_ethercat_slaves"
      fi
    else
      fail "EtherCAT master is inaccessible: $ethercat_output"
    fi
  else
    fail "ethercat CLI is unavailable"
  fi
fi

validator="$workspace_root/spear_bringup/spear_bringup/config_validator.py"
if ! python3 -c 'import yaml' >/dev/null 2>&1; then
  fail "Python YAML support is unavailable; install python3-yaml"
elif [ -f "$validator" ]; then
  if python3 "$validator" \
    --drive-config "$workspace_root/spear_drive/config/drive_controller.yaml" \
    --actuator-map "$workspace_root/spear_drive/config/actuator_map.yaml" \
    --brushed-config "$workspace_root/spear_drive/config/brushed_dc_config.yaml" \
    --stepper-config "$workspace_root/plex_ethercat/config/stepper_config.yaml"; then
    pass "static drive and EtherCAT configuration contracts are valid"
  else
    fail "competition configuration validation failed"
  fi
else
  fail "competition configuration validator is missing"
fi

printf '\nPreflight result: %d failure(s), %d warning(s)\n' "$failures" "$warnings"
if [ "$failures" -ne 0 ]; then
  exit 1
fi
