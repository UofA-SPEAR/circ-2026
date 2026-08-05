"""Dependency-free NMEA helpers for the Ultimate GPS driver."""

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
import math
from typing import List, Optional, Tuple


KNOTS_TO_METERS_PER_SECOND = 0.514444


class NmeaError(ValueError):
    """Raised when an NMEA sentence is malformed or fails validation."""


class NmeaChecksumError(NmeaError):
    """Raised when an NMEA checksum is absent or incorrect."""


@dataclass(frozen=True)
class GgaFix:
    """Position and fix-quality fields from a GGA sentence."""

    talker: str
    utc_time: Optional[time]
    latitude: float
    longitude: float
    quality: int
    satellites: int
    hdop: float
    altitude_msl: float
    geoid_separation: float

    @property
    def valid(self) -> bool:
        return (
            self.quality > 0
            and math.isfinite(self.latitude)
            and math.isfinite(self.longitude)
        )

    @property
    def altitude_ellipsoid(self) -> float:
        """Return WGS-84 ellipsoid height, as required by NavSatFix."""
        if not math.isfinite(self.altitude_msl):
            return math.nan
        if not math.isfinite(self.geoid_separation):
            return self.altitude_msl
        return self.altitude_msl + self.geoid_separation


@dataclass(frozen=True)
class RmcFix:
    """Time, position, speed, and course fields from an RMC sentence."""

    talker: str
    timestamp: Optional[datetime]
    valid: bool
    latitude: float
    longitude: float
    speed_mps: float
    course_deg: float


@dataclass(frozen=True)
class PmtkAck:
    """Acknowledgement returned by the MTK3339 for a PMTK command."""

    command: int
    flag: int

    @property
    def successful(self) -> bool:
        return self.flag == 3


def _checksum(payload: str) -> int:
    value = 0
    for character in payload:
        value ^= ord(character)
    return value


def add_checksum(payload: str) -> bytes:
    """Return a checksummed NMEA/PMTK command terminated with CRLF."""
    clean_payload = payload.strip().removeprefix("$").split("*", 1)[0]
    if not clean_payload:
        raise NmeaError("cannot checksum an empty payload")
    return (
        f"${clean_payload}*{_checksum(clean_payload):02X}\r\n".encode("ascii")
    )


def split_sentence(sentence: str) -> Tuple[str, List[str]]:
    """Validate a sentence and return its payload and comma-separated fields."""
    clean_sentence = sentence.strip()
    if not clean_sentence.startswith("$"):
        raise NmeaError("sentence does not start with '$'")
    if "*" not in clean_sentence:
        raise NmeaChecksumError("sentence has no checksum")

    payload, checksum_text = clean_sentence[1:].rsplit("*", 1)
    if len(checksum_text) < 2:
        raise NmeaChecksumError("checksum is incomplete")
    try:
        supplied_checksum = int(checksum_text[:2], 16)
    except ValueError as error:
        raise NmeaChecksumError("checksum is not hexadecimal") from error

    computed_checksum = _checksum(payload)
    if supplied_checksum != computed_checksum:
        raise NmeaChecksumError(
            f"checksum mismatch: received {supplied_checksum:02X}, "
            f"computed {computed_checksum:02X}"
        )
    return payload, payload.split(",")


def checksum_ok(sentence: str) -> bool:
    """Return whether a sentence is well formed and has a correct checksum."""
    try:
        split_sentence(sentence)
        return True
    except NmeaError:
        return False


def sentence_type(sentence: str) -> str:
    """Return GGA, RMC, PMTK001, or the comparable sentence identifier."""
    _, fields = split_sentence(sentence)
    identifier = fields[0]
    if identifier.startswith("PMTK"):
        return identifier
    return identifier[-3:] if len(identifier) >= 3 else identifier


def _float(value: str, default: float = math.nan) -> float:
    return float(value) if value else default


def _int(value: str, default: int = 0) -> int:
    return int(value) if value else default


def _coordinate(
    value: str,
    hemisphere: str,
    maximum: float,
    valid_hemispheres: Tuple[str, str],
) -> float:
    if not value and not hemisphere:
        return math.nan
    if not value or hemisphere not in valid_hemispheres:
        raise NmeaError("coordinate or hemisphere is incomplete")

    try:
        raw_value = float(value)
    except ValueError as error:
        raise NmeaError("coordinate is not numeric") from error

    degrees = int(raw_value / 100)
    minutes = raw_value - degrees * 100
    if minutes < 0.0 or minutes >= 60.0:
        raise NmeaError("coordinate minutes are outside [0, 60)")

    decimal_degrees = degrees + minutes / 60.0
    if decimal_degrees > maximum:
        raise NmeaError("coordinate degrees exceed their valid range")
    if hemisphere in ("S", "W"):
        decimal_degrees = -decimal_degrees
    return decimal_degrees


def _utc_time(value: str) -> Optional[time]:
    if not value:
        return None
    if len(value) < 6:
        raise NmeaError("UTC time is incomplete")
    try:
        hour = int(value[0:2])
        minute = int(value[2:4])
        raw_seconds = float(value[4:])
        second = int(raw_seconds)
        microsecond = round((raw_seconds - second) * 1_000_000)
        return time(
            hour,
            minute,
            second,
            microsecond,
            tzinfo=timezone.utc,
        )
    except (ValueError, OverflowError) as error:
        raise NmeaError("UTC time is invalid") from error


def _utc_datetime(time_value: str, date_value: str) -> Optional[datetime]:
    parsed_time = _utc_time(time_value)
    if parsed_time is None and not date_value:
        return None
    if parsed_time is None or len(date_value) != 6:
        raise NmeaError("RMC date or time is incomplete")

    try:
        short_year = int(date_value[4:6])
        year = 1900 + short_year if short_year >= 80 else 2000 + short_year
        parsed_date = date(
            year,
            int(date_value[2:4]),
            int(date_value[0:2]),
        )
        return datetime.combine(parsed_date, parsed_time)
    except ValueError as error:
        raise NmeaError("RMC date is invalid") from error


def parse_gga(sentence: str) -> GgaFix:
    """Parse a checksummed GP/GN/other-talker GGA sentence."""
    _, fields = split_sentence(sentence)
    if not fields[0].endswith("GGA"):
        raise NmeaError("sentence is not GGA")
    if len(fields) < 15:
        raise NmeaError("GGA sentence has too few fields")

    try:
        return GgaFix(
            talker=fields[0][:-3],
            utc_time=_utc_time(fields[1]),
            latitude=_coordinate(fields[2], fields[3], 90.0, ("N", "S")),
            longitude=_coordinate(fields[4], fields[5], 180.0, ("E", "W")),
            quality=_int(fields[6]),
            satellites=_int(fields[7]),
            hdop=_float(fields[8]),
            altitude_msl=_float(fields[9]),
            geoid_separation=_float(fields[11]),
        )
    except (ValueError, IndexError) as error:
        raise NmeaError("GGA contains an invalid numeric field") from error


def parse_rmc(sentence: str) -> RmcFix:
    """Parse a checksummed GP/GN/other-talker RMC sentence."""
    _, fields = split_sentence(sentence)
    if not fields[0].endswith("RMC"):
        raise NmeaError("sentence is not RMC")
    if len(fields) < 10:
        raise NmeaError("RMC sentence has too few fields")

    try:
        status = fields[2]
        if status not in ("A", "V"):
            raise NmeaError("RMC status is neither active nor void")
        return RmcFix(
            talker=fields[0][:-3],
            timestamp=_utc_datetime(fields[1], fields[9]),
            valid=status == "A",
            latitude=_coordinate(fields[3], fields[4], 90.0, ("N", "S")),
            longitude=_coordinate(fields[5], fields[6], 180.0, ("E", "W")),
            speed_mps=_float(fields[7]) * KNOTS_TO_METERS_PER_SECOND,
            course_deg=_float(fields[8]),
        )
    except (ValueError, IndexError) as error:
        raise NmeaError("RMC contains an invalid numeric field") from error


def parse_pmtk_ack(sentence: str) -> PmtkAck:
    """Parse `$PMTK001,<command>,<flag>` receiver acknowledgement."""
    _, fields = split_sentence(sentence)
    if fields[0] != "PMTK001":
        raise NmeaError("sentence is not a PMTK acknowledgement")
    if len(fields) < 3:
        raise NmeaError("PMTK acknowledgement has too few fields")
    try:
        return PmtkAck(command=int(fields[1]), flag=int(fields[2]))
    except ValueError as error:
        raise NmeaError("PMTK acknowledgement is invalid") from error
