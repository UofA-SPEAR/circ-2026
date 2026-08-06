"""Run a competition rosbag with explicit duration and storage limits."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Iterable, Optional, Sequence


DEFAULT_TOPICS = (
    "/diagnostics",
    "/drive/joy",
    "/drive_teleop/diagnostics",
    "/joy",
    "/joint_states",
    "/rosout",
    "/tf",
    "/tf_static",
    "/arm/teleop/status",
    "/gps/fix",
    "/gps/mission/status",
    "/gps/nmea",
    "/gps/time_reference",
    "/gps/velocity",
    "/spear_drive_controller/cmd_vel",
    "/spear_drive_controller/diagnostics",
    "/spear_drive_controller/imu",
    "/spear_drive_controller/odom",
    "/velocity_controller/commands",
)


def directory_size_bytes(path: Path) -> int:
    """Return the current size of regular files below path."""
    if not path.exists():
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for filename in files:
            candidate = Path(root) / filename
            try:
                total += candidate.stat().st_size
            except FileNotFoundError:
                # rosbag may rotate a file between os.walk and stat.
                continue
    return total


def build_record_command(
    output_directory: Path,
    topics: Iterable[str],
    max_bagfile_size_bytes: int,
) -> list[str]:
    """Build the ROS 2 Humble-compatible bag recording command."""
    return [
        "ros2",
        "bag",
        "record",
        "--output",
        str(output_directory),
        "--max-bag-size",
        str(max_bagfile_size_bytes),
        *topics,
    ]


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0.0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def _unique_output_directory(root: Path, prefix: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"{prefix}_{timestamp}"
    candidate = base
    suffix = 1
    while candidate.exists():
        candidate = Path(f"{base}_{suffix}")
        suffix += 1
    return candidate


def _stop_process(process: subprocess.Popen, grace_seconds: float = 10.0) -> None:
    """Request a clean rosbag metadata flush, then force exit if necessary."""
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3.0)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record competition telemetry and stop cleanly at the configured "
            "duration or size limit. Camera video is deliberately excluded."
        )
    )
    parser.add_argument("--output-root", default="~/.ros/spear_bags")
    parser.add_argument("--session-prefix", default="circ_rover")
    parser.add_argument("--max-duration-sec", type=_positive_float, default=7200.0)
    parser.add_argument("--max-total-size-mb", type=_positive_int, default=10240)
    parser.add_argument("--max-bagfile-size-mb", type=_positive_int, default=1024)
    parser.add_argument("--poll-seconds", type=_positive_float, default=1.0)
    parser.add_argument(
        "--topic",
        action="append",
        dest="topics",
        help="Topic to record; repeat to replace the competition default list",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Record until stopped by launch or a configured resource limit."""
    arguments = _parser().parse_args(argv)
    output_root = Path(arguments.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    output_directory = _unique_output_directory(
        output_root,
        arguments.session_prefix,
    )

    topics = tuple(arguments.topics or DEFAULT_TOPICS)
    megabyte = 1024 * 1024
    command = build_record_command(
        output_directory,
        topics,
        arguments.max_bagfile_size_mb * megabyte,
    )
    stop_requested = False

    def request_stop(_signum, _frame):
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    print(f"Recording competition telemetry to {output_directory}", flush=True)
    print(
        "Limits: "
        f"{arguments.max_duration_sec:.0f} s, "
        f"{arguments.max_total_size_mb} MiB total",
        flush=True,
    )
    try:
        process = subprocess.Popen(command, start_new_session=True)
    except FileNotFoundError:
        print("ERROR: ros2 executable is unavailable", file=sys.stderr)
        return 127

    started = time.monotonic()
    stop_reason = ""
    try:
        while process.poll() is None:
            elapsed = time.monotonic() - started
            size_bytes = directory_size_bytes(output_directory)
            if stop_requested:
                stop_reason = "launch shutdown requested"
                break
            if elapsed >= arguments.max_duration_sec:
                stop_reason = "maximum recording duration reached"
                break
            if size_bytes >= arguments.max_total_size_mb * megabyte:
                stop_reason = "maximum recording size reached"
                break
            time.sleep(arguments.poll_seconds)
    finally:
        if process.poll() is None:
            print(f"Stopping recorder: {stop_reason}", flush=True)
            _stop_process(process)

    return_code = process.poll()
    if stop_reason:
        print(
            f"Recorder stopped cleanly ({stop_reason}); "
            f"size={directory_size_bytes(output_directory)} bytes",
            flush=True,
        )
        return 0
    if return_code:
        print(f"ERROR: ros2 bag exited with code {return_code}", file=sys.stderr)
        return int(return_code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
