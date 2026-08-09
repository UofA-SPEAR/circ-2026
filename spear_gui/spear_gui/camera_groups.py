"""Static rover camera inventory and process grouping.

The Jetson can encode all eight streams, but creating eight independent ZED /
GStreamer process contexts exhausts a native multimedia resource on the
deployed L4T 36.4 system.  Two pipelines per process keeps four independent
failure domains while leaving substantially more headroom for NVENC, Argus,
CUDA, and ZED SDK process-local state.
"""


CAMERA_GROUPS = (
    (
        {"camera_sn": 302801647, "source": "zedxonesrc", "port": 5000,
         "exposure": 10000, "gain": 30000},
        {"camera_sn": 303928833, "source": "zedxonesrc", "port": 5001,
         "exposure": 10000, "gain": 30000},
    ),
    (
        {"camera_sn": 305325257, "source": "zedxonesrc", "port": 5002,
         "exposure": 10000, "gain": 30000},
        {"camera_sn": 307142683, "source": "zedxonesrc", "port": 5003,
         "exposure": 10000, "gain": 30000},
    ),
    (
        {"camera_sn": 308873104, "source": "zedxonesrc", "port": 5004,
         "exposure": 10000, "gain": 30000},
        {"camera_sn": 309256978, "source": "zedxonesrc", "port": 5005,
         "exposure": 10000, "gain": 30000},
    ),
    (
        {"camera_sn": 44249482, "source": "zedsrc", "port": 5006,
         "exposure": 10000, "gain": 30000},
        {"camera_sn": 58896881, "source": "zedsrc", "port": 5007,
         "exposure": 10000, "gain": 30000},
    ),
)


def get_camera_group(group_index):
    """Return one validated two-camera process group."""
    try:
        return CAMERA_GROUPS[int(group_index)]
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            f"group_index must be between 0 and {len(CAMERA_GROUPS) - 1}"
        ) from exc
