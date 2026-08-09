#!/usr/bin/env bash
#
# circ-tmux.sh — build the circ-2026 debugging session
#
#   Windows:
#     1. joints      — 4x joint_states echoes           (tiled)
#     2. controllers — 4x controller command echoes     (tiled)
#     3. main        — ethercat slaves + 3 free shells  (tiled)
#     4. camera      — single sourced shell
#     5. joy         — joy_drive / joy_arm              (side by side)
#
# Topic types are passed explicitly so `ros2 topic echo` subscribes and waits
# quietly instead of erroring out when nothing is publishing yet.
#
# Re-running attaches to the existing session instead of rebuilding it.

set -euo pipefail

SESSION="circ"
WORKDIR="$HOME/circ-2026"

# Set to 1 if `ros2 topic echo` can't import a message type.
# (Needed when the workspace defines its own msg/srv packages and your
#  .bashrc only sources /opt/ros/<distro>.)
SOURCE_WS=0

# Message types — verify with `ros2 topic type <topic>` once things are live.
JOINT_STATE="sensor_msgs/msg/JointState"
DYN_JOINT_STATE="control_msgs/msg/DynamicJointState"
CMD="std_msgs/msg/Float64MultiArray"
JOY="sensor_msgs/msg/Joy"

# ---------------------------------------------------------------- helpers ---

# Prefix ros2 commands with a workspace source when SOURCE_WS=1.
ros_cmd() {
    if [[ "$SOURCE_WS" -eq 1 ]]; then
        printf 'source install/setup.bash && %s' "$1"
    else
        printf '%s' "$1"
    fi
}

# new_window <name> -> prints the pane id of the window's first pane
new_window() {
    tmux new-window -d -t "$SESSION" -n "$1" -c "$WORKDIR" -P -F '#{pane_id}'
}

# split <target-pane> [-h|-v] -> prints the pane id of the new pane
split() {
    tmux split-window -d -t "$1" "${2:--v}" -c "$WORKDIR" -P -F '#{pane_id}'
}

# echo_topic <pane-id> <topic> <type>
echo_topic() {
    tmux send-keys -t "$1" "$(ros_cmd "ros2 topic echo $2 $3")" C-m
}

# run <pane-id> <command>
run() {
    tmux send-keys -t "$1" "$2" C-m
}

# tile <window-name>
tile() {
    tmux select-layout -t "$SESSION:$1" tiled >/dev/null
}

# ------------------------------------------------------------------- guard ---

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists — attaching."
    exec tmux attach -t "$SESSION"
fi

if [[ ! -d "$WORKDIR" ]]; then
    echo "warning: $WORKDIR does not exist" >&2
fi

# --------------------------------------------------- 1. joint state topics ---

tmux new-session -d -s "$SESSION" -n joints -c "$WORKDIR"
j0=$(tmux display-message -p -t "$SESSION:joints" '#{pane_id}')
j1=$(split "$j0" -h)
j2=$(split "$j0" -v)
j3=$(split "$j1" -v)

echo_topic "$j0" "jsb_drive/joint_states"            "$JOINT_STATE"
echo_topic "$j1" "jsb_steer/joint_states"            "$JOINT_STATE"
echo_topic "$j2" "/joint_states"                     "$JOINT_STATE"
echo_topic "$j3" "jsb_gripper/dynamic_joint_states"  "$DYN_JOINT_STATE"
tile joints

# ---------------------------------------------------- 2. controller topics ---

c0=$(new_window controllers)
c1=$(split "$c0" -h)
c2=$(split "$c0" -v)
c3=$(split "$c1" -v)

echo_topic "$c0" "drive_velocity_controller/commands"   "$CMD"
echo_topic "$c1" "steer_position_controller/commands"   "$CMD"
echo_topic "$c2" "velocity_controller/commands"         "$CMD"
echo_topic "$c3" "gripper_current_controller/commands"  "$CMD"
tile controllers

# ------------------------------------------------------------- 3. main ------

m0=$(new_window main)
m1=$(split "$m0" -h)
m2=$(split "$m0" -v)
m3=$(split "$m1" -v)

run "$m0" 'watch -n 0.1 ethercat slaves'
for p in "$m1" "$m2" "$m3"; do
    run "$p" 'source install/setup.bash'
done
tile main

# ----------------------------------------------------------- 4. camera ------

cam=$(new_window camera)
run "$cam" 'source install/setup.bash'

# -------------------------------------------------------------- 5. joy ------

y0=$(new_window joy)
y1=$(split "$y0" -h)

echo_topic "$y0" "joy_drive" "$JOY"
echo_topic "$y1" "joy_arm"   "$JOY"

# ------------------------------------------------------------------ attach ---

tmux select-window -t "$SESSION:main"
tmux select-pane -t "$m0"
exec tmux attach -t "$SESSION"