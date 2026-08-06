"""Pure helpers for constructing rover camera GStreamer pipelines."""


SUPPORTED_SOURCES = {"zedxonesrc", "zedsrc"}


def build_pipeline(
    source,
    camera_sn,
    receiver_ip,
    port,
    bitrate,
    exposure,
    gain,
    camera_resolution=2,
    camera_fps=30,
    stream_type=0,
):
    """Build one explicitly configured, low-latency camera pipeline."""
    if source not in SUPPORTED_SOURCES:
        raise ValueError(
            f"unsupported camera source {source!r}; "
            f"expected one of {sorted(SUPPORTED_SOURCES)}"
        )

    mode_props = (
        f"camera-resolution={int(camera_resolution)} "
        f"camera-fps={int(camera_fps)} "
    )

    if source == "zedxonesrc":
        src_props = (
            f"camera-sn={int(camera_sn)} "
            f"{mode_props}"
            "ctrl-auto-exposure=false "
            f"ctrl-auto-exposure-range-min={int(exposure)} "
            f"ctrl-auto-exposure-range-max={int(exposure)} "
            f"ctrl-exposure-time={int(exposure)} "
            f"ctrl-analog-gain={int(gain)} "
        )
    else:
        # stream-type=0 sends the left image only. Depth is explicitly disabled
        # so the two stereo cameras do not allocate unnecessary GPU resources.
        src_props = (
            f"camera-sn={int(camera_sn)} "
            f"{mode_props}"
            f"stream-type={int(stream_type)} "
            "depth-mode=0 "
        )

    return (
        f"{source} name=src {src_props}"
        # One queued frame is enough for a real-time UDP stream. Keeping a
        # second full HD1200 NVMM buffer per pipeline wastes scarce native
        # multimedia memory when all eight encoders are active.
        "! queue max-size-buffers=1 leaky=downstream "
        "! videoconvert "
        "! video/x-raw,format=BGRx "
        "! nvvidconv "
        "! video/x-raw(memory:NVMM),format=NV12 "
        f"! nvv4l2h265enc bitrate={int(bitrate)} preset-level=2 "
        "! h265parse "
        "! rtph265pay name=pay config-interval=1 pt=96 "
        f"! udpsink host={receiver_ip} port={int(port)} sync=false async=false"
    )
