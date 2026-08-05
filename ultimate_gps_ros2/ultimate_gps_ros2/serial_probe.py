"""Command-line hardware probe for the Adafruit Ultimate GPS."""

import argparse
import math
import time

from .nmea import NmeaError, parse_gga, sentence_type


def _arguments():
    parser = argparse.ArgumentParser(
        description="Read and validate NMEA output without starting ROS 2"
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud-rate", type=int, default=9600)
    parser.add_argument("--duration", type=float, default=60.0)
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    try:
        import serial
    except ImportError:
        print("pyserial is not installed (sudo apt install python3-serial)")
        raise SystemExit(2)

    received = 0
    valid = 0
    valid_fixes = 0
    started = time.monotonic()
    try:
        with serial.Serial(
            arguments.port,
            arguments.baud_rate,
            timeout=1.0,
        ) as gps:
            print(
                f"Reading {arguments.port} at {arguments.baud_rate} baud "
                f"for {arguments.duration:.0f} seconds..."
            )
            while time.monotonic() - started < arguments.duration:
                raw_line = gps.readline()
                if not raw_line:
                    continue
                received += 1
                try:
                    sentence = raw_line.decode("ascii").strip()
                    message_type = sentence_type(sentence)
                    valid += 1
                    if message_type != "GGA":
                        continue
                    fix = parse_gga(sentence)
                    if fix.valid:
                        valid_fixes += 1
                    hdop = (
                        f"{fix.hdop:.1f}" if math.isfinite(fix.hdop) else "?"
                    )
                    latitude = (
                        f"{fix.latitude:.7f}"
                        if math.isfinite(fix.latitude)
                        else "searching"
                    )
                    longitude = (
                        f"{fix.longitude:.7f}"
                        if math.isfinite(fix.longitude)
                        else "searching"
                    )
                    print(
                        f"quality={fix.quality} satellites={fix.satellites} "
                        f"hdop={hdop} lat={latitude} lon={longitude}"
                    )
                except (UnicodeDecodeError, NmeaError):
                    continue
    except (serial.SerialException, OSError) as error:
        print(f"Could not read GPS: {error}")
        raise SystemExit(2)

    elapsed = max(0.001, time.monotonic() - started)
    print(
        f"Received {received} lines ({received / elapsed:.1f} Hz), "
        f"{valid} valid NMEA, {valid_fixes} valid GGA fixes"
    )
    if valid == 0:
        print("No valid NMEA received; check wiring, port, and 9600 baud")
        raise SystemExit(1)
    if valid_fixes == 0:
        print("NMEA works but there is no position fix; test outdoors")


if __name__ == "__main__":
    main()
