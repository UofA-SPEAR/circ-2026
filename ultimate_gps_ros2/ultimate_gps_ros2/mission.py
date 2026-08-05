"""Waypoint guidance and durable offline GPS session recording."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Iterable, List, Optional, Sequence, Tuple


EARTH_RADIUS_M = 6_371_000.0


class MissionError(ValueError):
    """Raised for invalid mission inputs or recorder operations."""


@dataclass(frozen=True)
class Waypoint:
    """A WGS-84 target and required direction of travel."""

    name: str
    latitude: float
    longitude: float
    approach_heading_deg: Optional[float] = None


@dataclass(frozen=True)
class FixSample:
    """One valid rover position and its associated quality data."""

    received_at_utc: str
    monotonic_time: float
    ros_stamp_sec: int
    ros_stamp_nanosec: int
    latitude: float
    longitude: float
    altitude_ellipsoid_m: float
    horizontal_sigma_m: float
    fix_quality: int
    satellites: int
    hdop: float
    speed_mps: float
    course_deg: float


@dataclass(frozen=True)
class Marker:
    """An averaged, named field location."""

    label: str
    captured_at_utc: str
    latitude: float
    longitude: float
    altitude_ellipsoid_m: float
    sample_count: int
    spread_m: float
    horizontal_sigma_m: float
    satellites: int
    hdop: float


def _finite_float(value: str, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise MissionError(f"{field} must be numeric") from error
    if not math.isfinite(result):
        raise MissionError(f"{field} must be finite")
    return result


def validate_coordinate(latitude: float, longitude: float) -> None:
    """Validate a decimal-degree WGS-84 coordinate."""
    if not -90.0 <= latitude <= 90.0:
        raise MissionError("latitude must be within [-90, 90]")
    if not -180.0 <= longitude <= 180.0:
        raise MissionError("longitude must be within [-180, 180]")


def load_waypoints_csv(path: str) -> List[Waypoint]:
    """Load ordered targets from a competition-friendly CSV file."""
    mission_path = Path(path).expanduser()
    if not mission_path.is_file():
        raise MissionError(f"waypoint file does not exist: {mission_path}")

    with mission_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {"name", "latitude", "longitude"}
        if reader.fieldnames is None or not required.issubset(
            set(reader.fieldnames)
        ):
            raise MissionError(
                "waypoint CSV needs name,latitude,longitude columns"
            )

        waypoints = []
        names = set()
        for row_number, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            if not name or name.startswith("#"):
                continue
            if name in names:
                raise MissionError(f"duplicate waypoint name: {name}")
            latitude = _finite_float(row.get("latitude"), "latitude")
            longitude = _finite_float(row.get("longitude"), "longitude")
            validate_coordinate(latitude, longitude)

            heading_text = (row.get("approach_heading_deg") or "").strip()
            heading = None
            if heading_text:
                heading = _finite_float(
                    heading_text,
                    "approach_heading_deg",
                )
                if not 0.0 <= heading < 360.0:
                    raise MissionError(
                        "approach_heading_deg must be within [0, 360)"
                    )
            waypoints.append(
                Waypoint(name, latitude, longitude, heading)
            )
            names.add(name)

    if not waypoints:
        raise MissionError("waypoint file contains no targets")
    return waypoints


def distance_and_bearing(
    latitude: float,
    longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> Tuple[float, float]:
    """Return great-circle distance and initial true bearing."""
    validate_coordinate(latitude, longitude)
    validate_coordinate(target_latitude, target_longitude)
    phi_1 = math.radians(latitude)
    phi_2 = math.radians(target_latitude)
    delta_phi = math.radians(target_latitude - latitude)
    delta_lambda = math.radians(target_longitude - longitude)
    haversine = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi_1)
        * math.cos(phi_2)
        * math.sin(delta_lambda / 2.0) ** 2
    )
    distance = 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(haversine))
    east = math.sin(delta_lambda) * math.cos(phi_2)
    north = (
        math.cos(phi_1) * math.sin(phi_2)
        - math.sin(phi_1) * math.cos(phi_2) * math.cos(delta_lambda)
    )
    bearing = math.degrees(math.atan2(east, north)) % 360.0
    return distance, bearing


def _mean_finite(values: Iterable[float]) -> float:
    finite_values = [value for value in values if math.isfinite(value)]
    if not finite_values:
        return math.nan
    return sum(finite_values) / len(finite_values)


def _max_finite(values: Iterable[float]) -> float:
    finite_values = [value for value in values if math.isfinite(value)]
    return max(finite_values) if finite_values else math.nan


def average_marker(label: str, samples: Sequence[FixSample]) -> Marker:
    """Average stationary fixes and report conservative quality values."""
    if not samples:
        raise MissionError("cannot capture a marker without valid fixes")
    latitude = sum(sample.latitude for sample in samples) / len(samples)
    longitude = sum(sample.longitude for sample in samples) / len(samples)
    spread = max(
        distance_and_bearing(
            latitude,
            longitude,
            sample.latitude,
            sample.longitude,
        )[0]
        for sample in samples
    )
    return Marker(
        label=label,
        captured_at_utc=datetime.now(timezone.utc).isoformat(),
        latitude=latitude,
        longitude=longitude,
        altitude_ellipsoid_m=_mean_finite(
            sample.altitude_ellipsoid_m for sample in samples
        ),
        sample_count=len(samples),
        spread_m=spread,
        horizontal_sigma_m=_max_finite(
            sample.horizontal_sigma_m for sample in samples
        ),
        satellites=min(sample.satellites for sample in samples),
        hdop=_max_finite(sample.hdop for sample in samples),
    )


def _json_value(value):
    return value if not isinstance(value, float) or math.isfinite(value) else None


class SessionRecorder:
    """Persist valid fixes, raw NMEA, markers, and GeoJSON onboard."""

    TRACK_FIELDS = tuple(FixSample.__dataclass_fields__)
    MARKER_FIELDS = tuple(Marker.__dataclass_fields__)

    def __init__(self, output_root: str, session_name: str) -> None:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", session_name).strip("_")
        safe_name = safe_name or "gps_session"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        root = Path(output_root).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        session_path = root / f"{timestamp}_{safe_name}"
        suffix = 1
        while session_path.exists():
            session_path = root / f"{timestamp}_{safe_name}_{suffix}"
            suffix += 1
        session_path.mkdir()
        self.path = session_path

        self._track_stream = (session_path / "track.csv").open(
            "w",
            newline="",
            encoding="utf-8",
            buffering=1,
        )
        self._marker_stream = (session_path / "markers.csv").open(
            "w",
            newline="",
            encoding="utf-8",
            buffering=1,
        )
        self._nmea_stream = (session_path / "raw_nmea.log").open(
            "w",
            encoding="ascii",
            errors="replace",
            buffering=1,
        )
        self._track_writer = csv.DictWriter(
            self._track_stream,
            fieldnames=self.TRACK_FIELDS,
        )
        self._marker_writer = csv.DictWriter(
            self._marker_stream,
            fieldnames=self.MARKER_FIELDS,
        )
        self._track_writer.writeheader()
        self._marker_writer.writeheader()
        self.samples: List[FixSample] = []
        self.markers: List[Marker] = []
        self._last_sync = time.monotonic()
        self._closed = False

    def append(self, sample: FixSample) -> None:
        """Append and flush a valid route point."""
        if self._closed:
            raise MissionError("session recorder is closed")
        self.samples.append(sample)
        self._track_writer.writerow(asdict(sample))
        self._track_stream.flush()
        if time.monotonic() - self._last_sync >= 1.0:
            os.fsync(self._track_stream.fileno())
            self._last_sync = time.monotonic()

    def append_nmea(self, received_at_utc: str, sentence: str) -> None:
        """Preserve the raw receiver stream for replay and debugging."""
        if self._closed:
            return
        self._nmea_stream.write(f"{received_at_utc} {sentence.strip()}\n")

    def capture(self, label: str, samples: Sequence[FixSample]) -> Marker:
        """Capture an averaged marker and persist it immediately."""
        if self._closed:
            raise MissionError("session recorder is closed")
        marker = average_marker(label, samples)
        self.markers.append(marker)
        self._marker_writer.writerow(asdict(marker))
        self._marker_stream.flush()
        self.export_geojson()
        return marker

    def export_geojson(self) -> Path:
        """Atomically update the offline route and marker export."""
        features = []
        if self.samples:
            features.append(
                {
                    "type": "Feature",
                    "properties": {"name": "actual_route"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [sample.longitude, sample.latitude]
                            for sample in self.samples
                        ],
                    },
                }
            )
        for marker in self.markers:
            properties = {
                key: _json_value(value)
                for key, value in asdict(marker).items()
                if key not in ("latitude", "longitude")
            }
            features.append(
                {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [marker.longitude, marker.latitude],
                    },
                }
            )
        document = {"type": "FeatureCollection", "features": features}
        destination = self.path / "route.geojson"
        temporary = self.path / ".route.geojson.tmp"
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(document, stream, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(destination)
        return destination

    def close(self) -> None:
        """Flush all artifacts and close the session."""
        if self._closed:
            return
        self.export_geojson()
        for stream in (
            self._track_stream,
            self._marker_stream,
            self._nmea_stream,
        ):
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
        self._closed = True
