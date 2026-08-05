#!/usr/bin/env bash
set -uo pipefail

failures=0
warnings=0
gps_port="${GPS_PORT:-/dev/ttyTHS1}"
waypoint_file="${WAYPOINT_FILE:-}"

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1"; warnings=$((warnings + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failures=$((failures + 1)); }

if command -v ros2 >/dev/null 2>&1; then
  pass "ros2 is available"
else
  fail "ros2 is unavailable; source /opt/ros/humble/setup.bash"
fi

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

available_kb=$(df -Pk . | awk 'NR==2 {print $4}')
if [ "${available_kb:-0}" -ge 5242880 ]; then
  pass "at least 5 GiB of workspace storage is free"
else
  warn "less than 5 GiB of workspace storage is free"
fi

if [ -n "$waypoint_file" ]; then
  if [ -f "$waypoint_file" ]; then
    rows=$(awk -F, 'NR > 1 && $1 !~ /^#/ && $1 != "" {count++} END {print count+0}' "$waypoint_file")
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

for package in ultimate_gps_ros2 spear_gui plex_moveit spear_bringup; do
  if command -v ros2 >/dev/null 2>&1 && ros2 pkg prefix "$package" >/dev/null 2>&1; then
    pass "ROS package installed: $package"
  else
    fail "ROS package unavailable: $package"
  fi
done

printf '\nPreflight result: %d failure(s), %d warning(s)\n' "$failures" "$warnings"
if [ "$failures" -ne 0 ]; then
  exit 1
fi
