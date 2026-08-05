"""Generate an offline report map from a recorded GPS session."""

import argparse
import json
import math
from pathlib import Path


def _arguments():
    parser = argparse.ArgumentParser(
        description="Render route.geojson as a report-ready PNG or PDF"
    )
    parser.add_argument("session", help="Session directory or route.geojson")
    parser.add_argument("--output", default="", help="Output .png or .pdf")
    parser.add_argument("--title", default="CIRC actual rover route")
    return parser.parse_args()


def _load_features(path: Path):
    with path.open(encoding="utf-8") as stream:
        document = json.load(stream)
    route = []
    markers = []
    for feature in document.get("features", []):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") == "LineString":
            route = geometry.get("coordinates") or []
        elif geometry.get("type") == "Point":
            markers.append(
                (
                    feature.get("properties", {}).get("label", "marker"),
                    geometry.get("coordinates"),
                )
            )
    if not route:
        raise ValueError("GeoJSON contains no recorded route")
    return route, markers


def _to_local_meters(coordinates, latitude_origin, longitude_origin):
    meters_per_degree_latitude = 111_320.0
    meters_per_degree_longitude = (
        meters_per_degree_latitude * math.cos(math.radians(latitude_origin))
    )
    return [
        (
            (longitude - longitude_origin) * meters_per_degree_longitude,
            (latitude - latitude_origin) * meters_per_degree_latitude,
        )
        for longitude, latitude in coordinates
    ]


def _scale_length(span: float) -> float:
    target = max(1.0, span * 0.2)
    magnitude = 10 ** math.floor(math.log10(target))
    for multiplier in (1, 2, 5, 10):
        candidate = multiplier * magnitude
        if candidate >= target:
            return candidate
    return 10 * magnitude


def main() -> None:
    arguments = _arguments()
    session = Path(arguments.session).expanduser()
    source = session / "route.geojson" if session.is_dir() else session
    if not source.is_file():
        raise SystemExit(f"Route file not found: {source}")
    destination = (
        Path(arguments.output).expanduser()
        if arguments.output
        else source.with_name("route_map.png")
    )
    if destination.suffix.lower() not in (".png", ".pdf"):
        raise SystemExit("Output must end in .png or .pdf")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plot
    except ImportError as error:
        raise SystemExit(
            "matplotlib is required (sudo apt install python3-matplotlib)"
        ) from error

    route, markers = _load_features(source)
    longitude_origin, latitude_origin = route[0]
    local_route = _to_local_meters(
        route,
        latitude_origin,
        longitude_origin,
    )
    x_values = [point[0] for point in local_route]
    y_values = [point[1] for point in local_route]

    figure, axes = plot.subplots(figsize=(10, 8))
    axes.plot(x_values, y_values, color="#7257d6", linewidth=2, label="Route")
    axes.scatter(x_values[0], y_values[0], marker="s", color="black", zorder=3)
    for label, coordinate in markers:
        if not coordinate or len(coordinate) < 2:
            continue
        local = _to_local_meters(
            [coordinate],
            latitude_origin,
            longitude_origin,
        )[0]
        axes.scatter(local[0], local[1], s=55, zorder=4)
        axes.annotate(
            label,
            local,
            xytext=(5, 5),
            textcoords="offset points",
        )

    x_span = max(x_values) - min(x_values)
    y_span = max(y_values) - min(y_values)
    span = max(10.0, x_span, y_span)
    scale = _scale_length(span)
    x_start = min(x_values) + span * 0.05
    y_start = min(y_values) + span * 0.05
    axes.plot(
        [x_start, x_start + scale],
        [y_start, y_start],
        color="black",
        linewidth=4,
    )
    axes.text(x_start + scale / 2.0, y_start, f" {scale:g} m", va="bottom")
    axes.annotate(
        "N",
        xy=(0.94, 0.92),
        xytext=(0.94, 0.78),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "linewidth": 2},
        ha="center",
        fontsize=13,
        fontweight="bold",
    )
    axes.set_title(
        f"{arguments.title}\n"
        f"Origin: {latitude_origin:.7f}, {longitude_origin:.7f} (WGS-84)"
    )
    axes.set_xlabel("East of start (m)")
    axes.set_ylabel("North of start (m)")
    axes.grid(True, alpha=0.35)
    axes.set_aspect("equal", adjustable="datalim")
    axes.legend(loc="best")
    figure.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=200)
    plot.close(figure)
    print(destination)


if __name__ == "__main__":
    main()
