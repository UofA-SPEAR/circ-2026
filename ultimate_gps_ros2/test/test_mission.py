import csv
import json
import math

import pytest

from ultimate_gps_ros2.mission import (
    FixSample,
    MissionError,
    SessionRecorder,
    average_marker,
    distance_and_bearing,
    load_waypoints_csv,
)


def _sample(monotonic_time=1.0, latitude=51.0, longitude=-112.0):
    return FixSample(
        received_at_utc="2026-08-05T12:00:00+00:00",
        monotonic_time=monotonic_time,
        ros_stamp_sec=1,
        ros_stamp_nanosec=2,
        latitude=latitude,
        longitude=longitude,
        altitude_ellipsoid_m=700.0,
        horizontal_sigma_m=2.0,
        fix_quality=1,
        satellites=9,
        hdop=0.8,
        speed_mps=0.0,
        course_deg=0.0,
    )


def test_distance_and_bearing_reference():
    distance, bearing = distance_and_bearing(0.0, 0.0, 0.0, 0.001)
    assert distance == pytest.approx(111.195, abs=0.01)
    assert bearing == pytest.approx(90.0)


def test_load_ordered_waypoints(tmp_path):
    path = tmp_path / "waypoints.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["name", "latitude", "longitude", "approach_heading_deg"]
        )
        writer.writerow(["gate_1", "51.0000001", "-112.0", "90"])
        writer.writerow(["gate_2", "51.0001001", "-112.0", "180"])
    waypoints = load_waypoints_csv(str(path))
    assert [waypoint.name for waypoint in waypoints] == ["gate_1", "gate_2"]
    assert waypoints[0].approach_heading_deg == 90.0


def test_reject_invalid_waypoint(tmp_path):
    path = tmp_path / "waypoints.csv"
    path.write_text("name,latitude,longitude\ngate,100,-112\n")
    with pytest.raises(MissionError):
        load_waypoints_csv(str(path))


def test_average_marker_reports_spread():
    marker = average_marker(
        "site_1",
        [_sample(), _sample(latitude=51.00001)],
    )
    assert marker.sample_count == 2
    assert marker.spread_m > 0.0
    assert math.isfinite(marker.latitude)


def test_recorder_writes_offline_artifacts(tmp_path):
    recorder = SessionRecorder(str(tmp_path), "test/session")
    samples = [_sample(), _sample(2.0, 51.00001)]
    for sample in samples:
        recorder.append(sample)
    recorder.append_nmea("2026-08-05T12:00:00+00:00", "$GPGGA,test")
    recorder.capture("site_1", samples)
    recorder.close()

    assert (recorder.path / "track.csv").is_file()
    assert (recorder.path / "markers.csv").is_file()
    assert (recorder.path / "raw_nmea.log").is_file()
    geojson = json.loads((recorder.path / "route.geojson").read_text())
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 2
