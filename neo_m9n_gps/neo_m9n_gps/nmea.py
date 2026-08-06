"""Small, dependency-free parser for the NEO-M9N factory NMEA output."""

from dataclasses import dataclass
import math
from typing import Optional, Sequence


KNOTS_TO_METERS_PER_SECOND = 0.5144444444444445


class NmeaError(ValueError):
    """Base class for rejected NMEA sentences."""


class NmeaChecksumError(NmeaError):
    """Raised when a sentence checksum is missing or incorrect."""


@dataclass(frozen=True)
class NmeaSentence:
    """A checksum-validated NMEA sentence."""

    talker: str
    message_type: str
    fields: tuple[str, ...]
    raw: str


@dataclass
class GpsState:
    """Latest navigation fields assembled from multiple NMEA sentences."""

    latitude_deg: Optional[float] = None
    longitude_deg: Optional[float] = None
    altitude_msl_m: Optional[float] = None
    geoid_separation_m: Optional[float] = None
    fix_quality: int = 0
    satellites: int = 0
    hdop: Optional[float] = None
    vdop: Optional[float] = None
    pdop: Optional[float] = None
    speed_mps: Optional[float] = None
    course_deg: Optional[float] = None
    utc_time: str = ''
    utc_date: str = ''
    rmc_valid: bool = False
    gsa_fix_type: int = 1
    receiver_text: str = ''

    @property
    def has_fix(self) -> bool:
        """Return true only when the receiver reports a usable position."""
        return (
            self.fix_quality > 0
            and self.latitude_deg is not None
            and self.longitude_deg is not None
        )

    @property
    def altitude_ellipsoid_m(self) -> Optional[float]:
        """Convert GGA mean-sea-level altitude to WGS84 ellipsoid altitude."""
        if self.altitude_msl_m is None:
            return None
        if self.geoid_separation_m is None:
            return self.altitude_msl_m
        return self.altitude_msl_m + self.geoid_separation_m

    def update(self, sentence: NmeaSentence) -> str:
        """Apply a supported sentence and return its message type."""
        handlers = {
            'GGA': self._update_gga,
            'GSA': self._update_gsa,
            'RMC': self._update_rmc,
            'TXT': self._update_txt,
            'VTG': self._update_vtg,
        }
        handler = handlers.get(sentence.message_type)
        if handler is not None:
            handler(sentence.fields)
        return sentence.message_type

    def _update_gga(self, fields: Sequence[str]) -> None:
        _require_fields(fields, 11, 'GGA')
        self.utc_time = fields[0]
        self.fix_quality = _to_int(fields[5], default=0)
        self.satellites = _to_int(fields[6], default=0)
        self.hdop = _to_float(fields[7])
        self.altitude_msl_m = _to_float(fields[8])
        self.geoid_separation_m = _to_float(fields[10])

        if fields[1] and fields[2] and fields[3] and fields[4]:
            self.latitude_deg = parse_coordinate(fields[1], fields[2], True)
            self.longitude_deg = parse_coordinate(fields[3], fields[4], False)
        else:
            self.latitude_deg = None
            self.longitude_deg = None

    def _update_gsa(self, fields: Sequence[str]) -> None:
        _require_fields(fields, 17, 'GSA')
        self.gsa_fix_type = _to_int(fields[1], default=1)
        self.pdop = _to_float(fields[14])
        hdop = _to_float(fields[15])
        if hdop is not None:
            self.hdop = hdop
        self.vdop = _to_float(fields[16])

    def _update_rmc(self, fields: Sequence[str]) -> None:
        _require_fields(fields, 9, 'RMC')
        self.utc_time = fields[0]
        self.rmc_valid = fields[1].upper() == 'A'
        self.speed_mps = _scaled_float(fields[6], KNOTS_TO_METERS_PER_SECOND)
        self.course_deg = _normalize_course(_to_float(fields[7]))
        self.utc_date = fields[8]

        if fields[2] and fields[3] and fields[4] and fields[5]:
            self.latitude_deg = parse_coordinate(fields[2], fields[3], True)
            self.longitude_deg = parse_coordinate(fields[4], fields[5], False)

    def _update_vtg(self, fields: Sequence[str]) -> None:
        _require_fields(fields, 7, 'VTG')
        course = _to_float(fields[0])
        speed_kmh = _to_float(fields[6])
        self.course_deg = _normalize_course(course)
        if speed_kmh is not None:
            self.speed_mps = speed_kmh / 3.6
        elif len(fields) > 4:
            self.speed_mps = _scaled_float(
                fields[4], KNOTS_TO_METERS_PER_SECOND
            )

    def _update_txt(self, fields: Sequence[str]) -> None:
        if fields:
            self.receiver_text = fields[-1]


def parse_sentence(raw: str) -> NmeaSentence:
    """Validate and split one NMEA sentence.

    Both two-character talkers such as ``GP`` and the multi-GNSS ``GN`` talker
    used by the NEO-M9N are accepted.
    """
    sentence = raw.strip()
    if not sentence.startswith('$'):
        raise NmeaError('sentence does not start with $')
    if '*' not in sentence:
        raise NmeaChecksumError('sentence has no checksum')

    payload, checksum_text = sentence[1:].rsplit('*', 1)
    if len(checksum_text) != 2:
        raise NmeaChecksumError('checksum must contain two hexadecimal digits')
    try:
        expected = int(checksum_text, 16)
    except ValueError as exc:
        raise NmeaChecksumError('checksum is not hexadecimal') from exc

    actual = nmea_checksum(payload)
    if actual != expected:
        raise NmeaChecksumError(
            f'checksum mismatch: expected {expected:02X}, calculated {actual:02X}'
        )

    parts = payload.split(',')
    identifier = parts[0]
    if len(identifier) < 5:
        raise NmeaError('sentence identifier is too short')

    return NmeaSentence(
        talker=identifier[:-3],
        message_type=identifier[-3:].upper(),
        fields=tuple(parts[1:]),
        raw=sentence,
    )


def nmea_checksum(payload: str) -> int:
    """Return the XOR checksum for text between ``$`` and ``*``."""
    checksum = 0
    for character in payload:
        checksum ^= ord(character)
    return checksum


def parse_coordinate(value: str, hemisphere: str, latitude: bool) -> float:
    """Convert NMEA degrees/minutes into signed decimal degrees."""
    degree_digits = 2 if latitude else 3
    if len(value) < degree_digits + 2:
        raise NmeaError('coordinate is too short')
    try:
        degrees = int(value[:degree_digits])
        minutes = float(value[degree_digits:])
    except ValueError as exc:
        raise NmeaError('coordinate contains a non-numeric value') from exc

    maximum = 90 if latitude else 180
    if (
        degrees > maximum
        or not 0.0 <= minutes < 60.0
        or (degrees == maximum and minutes > 0.0)
    ):
        raise NmeaError('coordinate is out of range')

    result = degrees + minutes / 60.0
    direction = hemisphere.upper()
    valid_directions = ('N', 'S') if latitude else ('E', 'W')
    if direction not in valid_directions:
        raise NmeaError('coordinate hemisphere is invalid')
    if direction in ('S', 'W'):
        result = -result
    return result


def enu_velocity(speed_mps: float, course_deg: float) -> tuple[float, float]:
    """Convert speed/course into east and north velocity components."""
    course_rad = math.radians(course_deg)
    east = speed_mps * math.sin(course_rad)
    north = speed_mps * math.cos(course_rad)
    return east, north


def covariance_from_dop(
    hdop: Optional[float],
    vdop: Optional[float],
    uere_m: float,
    minimum_sigma_m: float,
) -> tuple[float, ...]:
    """Estimate an ENU position covariance from DOP and assumed UERE."""
    horizontal_sigma = max((hdop or 1.0) * uere_m, minimum_sigma_m)
    vertical_sigma = max(
        (vdop * uere_m) if vdop is not None else horizontal_sigma * 2.0,
        minimum_sigma_m,
    )
    return (
        horizontal_sigma ** 2, 0.0, 0.0,
        0.0, horizontal_sigma ** 2, 0.0,
        0.0, 0.0, vertical_sigma ** 2,
    )


def _require_fields(fields: Sequence[str], count: int, message_type: str) -> None:
    if len(fields) < count:
        raise NmeaError(
            f'{message_type} has {len(fields)} fields; expected at least {count}'
        )


def _to_float(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        result = float(value)
    except ValueError as exc:
        raise NmeaError(f'invalid floating-point field: {value!r}') from exc
    if not math.isfinite(result):
        raise NmeaError('non-finite numeric field')
    return result


def _scaled_float(value: str, scale: float) -> Optional[float]:
    parsed = _to_float(value)
    return None if parsed is None else parsed * scale


def _to_int(value: str, default: int) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise NmeaError(f'invalid integer field: {value!r}') from exc


def _normalize_course(course: Optional[float]) -> Optional[float]:
    return None if course is None else course % 360.0
