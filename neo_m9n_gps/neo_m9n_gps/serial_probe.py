"""Discover serial devices that may contain a USB-connected GNSS receiver."""

import glob
import os
import sys
from typing import Iterable, Optional


DEFAULT_FALLBACK_PATTERNS = (
    '/dev/serial/by-id/*',
    '/dev/ttyACM*',
    '/dev/ttyUSB*',
)


def list_serial_ports() -> list[object]:
    """Return serial port metadata supplied by pyserial."""
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise RuntimeError(
            'pyserial is not installed; install the Ubuntu python3-serial package'
        ) from exc
    return list(list_ports.comports())


def select_serial_port(
    requested: str,
    fallback_patterns: Iterable[str] = DEFAULT_FALLBACK_PATTERNS,
) -> str:
    """Resolve an explicit path or conservatively auto-select one receiver."""
    if requested and requested.lower() != 'auto':
        return requested

    ports = list_serial_ports()
    identified = []
    for port in ports:
        searchable = ' '.join(
            str(getattr(port, field, '') or '')
            for field in ('description', 'manufacturer', 'product', 'hwid')
        ).lower()
        if any(token in searchable for token in ('u-blox', 'ublox', 'gnss', 'gps')):
            identified.append(str(port.device))

    identified = _unique(identified)
    if len(identified) == 1:
        return identified[0]
    if len(identified) > 1:
        raise RuntimeError(
            'multiple GNSS-like serial ports found; set the port parameter: '
            + ', '.join(identified)
        )

    fallback = []
    for pattern in fallback_patterns:
        fallback.extend(glob.glob(pattern))
    fallback = _unique_devices(fallback)
    if len(fallback) == 1:
        return fallback[0]
    if not fallback:
        raise RuntimeError(
            'no serial port found; connect the receiver or set port explicitly '
            '(for example /dev/ttyTHS0 for a Jetson GPIO UART)'
        )
    raise RuntimeError(
        'automatic selection is ambiguous; set the port parameter: '
        + ', '.join(fallback)
    )


def format_port(port: object) -> str:
    """Format one pyserial port for an operator."""
    device = str(getattr(port, 'device', 'unknown'))
    description = str(getattr(port, 'description', '') or 'no description')
    manufacturer = str(getattr(port, 'manufacturer', '') or 'unknown manufacturer')
    hwid = str(getattr(port, 'hwid', '') or 'unknown hardware ID')
    return f'{device}: {description}; {manufacturer}; {hwid}'


def main(args: Optional[list[str]] = None) -> int:
    """Print available ports and an automatic-selection recommendation."""
    del args
    try:
        ports = list_serial_ports()
    except RuntimeError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2

    if ports:
        print('Detected serial ports:')
        for port in ports:
            print(f'  {format_port(port)}')
    else:
        print('No pyserial ports were detected.')

    try:
        selected = select_serial_port('auto')
    except RuntimeError as exc:
        print(f'Auto-selection: {exc}')
        return 1
    print(f'Auto-selection: {selected}')
    return 0


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(sorted(values)))


def _unique_devices(values: Iterable[str]) -> list[str]:
    """Deduplicate stable symlinks and their underlying tty device."""
    devices = {}
    for value in sorted(values):
        devices.setdefault(os.path.realpath(value), value)
    return list(devices.values())


if __name__ == '__main__':
    raise SystemExit(main())
