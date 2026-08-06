from types import SimpleNamespace

import pytest

from neo_m9n_gps import serial_probe


def port(device, description='', manufacturer='', hwid=''):
    return SimpleNamespace(
        device=device,
        description=description,
        manufacturer=manufacturer,
        product='',
        hwid=hwid,
    )


def test_explicit_port_is_never_replaced(monkeypatch):
    monkeypatch.setattr(
        serial_probe,
        'list_serial_ports',
        lambda: (_ for _ in ()).throw(AssertionError('must not probe')),
    )
    assert serial_probe.select_serial_port('/dev/ttyTHS0') == '/dev/ttyTHS0'


def test_auto_selects_one_ublox_port(monkeypatch):
    monkeypatch.setattr(
        serial_probe,
        'list_serial_ports',
        lambda: [
            port('/dev/ttyUSB0', 'USB serial adapter'),
            port('/dev/ttyACM0', 'u-blox GNSS receiver'),
        ],
    )
    assert serial_probe.select_serial_port('auto', ()) == '/dev/ttyACM0'


def test_auto_refuses_multiple_gnss_ports(monkeypatch):
    monkeypatch.setattr(
        serial_probe,
        'list_serial_ports',
        lambda: [
            port('/dev/ttyACM0', 'u-blox GNSS receiver'),
            port('/dev/ttyACM1', 'GPS receiver'),
        ],
    )
    with pytest.raises(RuntimeError, match='multiple GNSS-like'):
        serial_probe.select_serial_port('auto', ())


def test_auto_refuses_ambiguous_fallback(monkeypatch):
    monkeypatch.setattr(serial_probe, 'list_serial_ports', lambda: [])
    monkeypatch.setattr(
        serial_probe.glob,
        'glob',
        lambda pattern: ['/dev/ttyUSB0', '/dev/ttyUSB1'],
    )
    with pytest.raises(RuntimeError, match='ambiguous'):
        serial_probe.select_serial_port('auto', ('/dev/ttyUSB*',))


def test_auto_deduplicates_device_symlink(monkeypatch):
    monkeypatch.setattr(serial_probe, 'list_serial_ports', lambda: [])
    monkeypatch.setattr(
        serial_probe.glob,
        'glob',
        lambda pattern: (
            ['/dev/serial/by-id/ublox']
            if 'by-id' in pattern
            else ['/dev/ttyACM0']
        ),
    )
    monkeypatch.setattr(
        serial_probe.os.path,
        'realpath',
        lambda path: '/dev/ttyACM0',
    )
    selected = serial_probe.select_serial_port(
        'auto', ('/dev/serial/by-id/*', '/dev/ttyACM*')
    )
    assert selected == '/dev/serial/by-id/ublox'
