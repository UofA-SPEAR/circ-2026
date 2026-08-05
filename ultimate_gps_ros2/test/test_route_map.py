from ultimate_gps_ros2.route_map import _scale_length, _to_local_meters


def test_local_coordinates_keep_origin_at_zero():
    points = _to_local_meters([[-112.0, 51.0]], 51.0, -112.0)
    assert points == [(0.0, 0.0)]


def test_scale_length_uses_readable_steps():
    assert _scale_length(100.0) == 20.0
    assert _scale_length(250.0) == 50.0
