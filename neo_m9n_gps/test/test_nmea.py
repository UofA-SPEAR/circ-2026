import math

import pytest

from neo_m9n_gps.nmea import (
    GpsState,
    NmeaChecksumError,
    NmeaError,
    covariance_from_dop,
    enu_velocity,
    nmea_checksum,
    parse_coordinate,
    parse_sentence,
)


def sentence(payload):
    return f'${payload}*{nmea_checksum(payload):02X}'


def test_parse_multi_gnss_gga_and_ellipsoid_altitude():
    raw = sentence(
        'GNGGA,165229.00,5321.68020,N,00630.33720,W,1,12,0.74,'
        '61.7,M,55.2,M,,')
    parsed = parse_sentence(raw)
    state = GpsState()
    state.update(parsed)

    assert parsed.talker == 'GN'
    assert parsed.message_type == 'GGA'
    assert state.has_fix
    assert state.satellites == 12
    assert state.latitude_deg == pytest.approx(53.3613366667)
    assert state.longitude_deg == pytest.approx(-6.50562)
    assert state.altitude_msl_m == pytest.approx(61.7)
    assert state.altitude_ellipsoid_m == pytest.approx(116.9)


def test_no_fix_gga_clears_coordinates():
    state = GpsState(latitude_deg=1.0, longitude_deg=2.0, fix_quality=1)
    state.update(parse_sentence(sentence(
        'GNGGA,165230.00,,,,,0,00,99.99,,,,,,')
    ))

    assert not state.has_fix
    assert state.latitude_deg is None
    assert state.longitude_deg is None
    assert state.fix_quality == 0


def test_rmc_velocity_and_course():
    state = GpsState()
    state.update(parse_sentence(sentence(
        'GNRMC,165229.00,A,5321.68020,N,00630.33720,W,10.0,90.0,'
        '050826,,,A,V')
    ))

    assert state.rmc_valid
    assert state.utc_date == '050826'
    assert state.speed_mps == pytest.approx(5.1444444444)
    assert state.course_deg == pytest.approx(90.0)
    east, north = enu_velocity(state.speed_mps, state.course_deg)
    assert east == pytest.approx(state.speed_mps)
    assert north == pytest.approx(0.0, abs=1e-12)


def test_gsa_updates_dilution_values():
    state = GpsState()
    state.update(parse_sentence(sentence(
        'GNGSA,A,3,04,05,09,12,24,25,29,31,,,,,1.8,1.0,1.5,1')
    ))

    assert state.gsa_fix_type == 3
    assert state.pdop == pytest.approx(1.8)
    assert state.hdop == pytest.approx(1.0)
    assert state.vdop == pytest.approx(1.5)


def test_vtg_is_velocity_fallback():
    state = GpsState()
    state.update(parse_sentence(sentence(
        'GNVTG,270.0,T,,M,3.0,N,5.556,K,A')
    ))

    assert state.course_deg == pytest.approx(270.0)
    assert state.speed_mps == pytest.approx(1.5433333333)


def test_bad_checksum_is_rejected():
    with pytest.raises(NmeaChecksumError):
        parse_sentence('$GNGGA,1,2,3*00')


@pytest.mark.parametrize(
    ('value', 'hemisphere', 'latitude', 'expected'),
    [
        ('9000.0000', 'N', True, 90.0),
        ('9000.0000', 'S', True, -90.0),
        ('18000.0000', 'E', False, 180.0),
        ('18000.0000', 'W', False, -180.0),
    ],
)
def test_coordinate_limits(value, hemisphere, latitude, expected):
    assert parse_coordinate(value, hemisphere, latitude) == expected


@pytest.mark.parametrize(
    ('value', 'hemisphere', 'latitude'),
    [
        ('9000.0001', 'N', True),
        ('18000.0001', 'E', False),
        ('1260.0000', 'N', True),
    ],
)
def test_out_of_range_coordinates_are_rejected(value, hemisphere, latitude):
    with pytest.raises(NmeaError, match='out of range'):
        parse_coordinate(value, hemisphere, latitude)


def test_covariance_from_dop():
    covariance = covariance_from_dop(0.8, 1.5, 3.0, 1.0)
    assert covariance[0] == pytest.approx(5.76)
    assert covariance[4] == pytest.approx(5.76)
    assert covariance[8] == pytest.approx(20.25)
    assert all(math.isfinite(value) for value in covariance)
