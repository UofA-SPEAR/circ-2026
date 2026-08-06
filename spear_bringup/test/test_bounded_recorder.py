"""Tests for bounded competition telemetry recording."""

from pathlib import Path

from spear_bringup.bounded_recorder import (
    DEFAULT_TOPICS,
    build_record_command,
    directory_size_bytes,
)


def test_directory_size_bytes_counts_nested_files(tmp_path):
    """All bag segments below a session directory count toward the limit."""
    (tmp_path / "metadata.yaml").write_bytes(b"1234")
    nested = tmp_path / "segments"
    nested.mkdir()
    (nested / "data.db3").write_bytes(b"123456")

    assert directory_size_bytes(tmp_path) == 10


def test_record_command_uses_explicit_output_size_and_topics():
    """The child rosbag command receives only intentional telemetry topics."""
    command = build_record_command(
        Path("/tmp/circ_bag"),
        ("/diagnostics", "/joint_states"),
        1048576,
    )

    assert command == [
        "ros2",
        "bag",
        "record",
        "--output",
        "/tmp/circ_bag",
        "--max-bag-size",
        "1048576",
        "/diagnostics",
        "/joint_states",
    ]


def test_default_topics_capture_control_but_exclude_camera_video():
    """Black-box telemetry stays useful without consuming camera bandwidth."""
    assert {
        "/diagnostics",
        "/drive/joy",
        "/drive_teleop/diagnostics",
        "/joy",
        "/joint_states",
        "/spear_drive_controller/cmd_vel",
        "/spear_drive_controller/odom",
    } <= set(DEFAULT_TOPICS)
    assert not [topic for topic in DEFAULT_TOPICS if "camera" in topic]
