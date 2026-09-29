#!/usr/bin/env python3
"""Compare two geographic coordinates and print the geodesic distance between them.

Accepted formats:
  - Decimal degrees:            48.8566, 2.3522   |   40.7128 -74.0060
  - Labeled:                    Latitude: 51.0407754, Longitude: -1.7588855
  - DMS:                        40°26'46"N 79°58'56"W
  - Degrees decimal minutes:    40°26.767'N 79°58.933'W
  - Geohash:                    u09tvw0f
"""

import argparse
import re
import sys

import pygeohash
from geopy.distance import geodesic

GEOHASH_RE = re.compile(r"^[0-9bcdefghjkmnpqrstuvwxyz]{4,12}$", re.IGNORECASE)

# labeled values, e.g. "Latitude: 51.04, Longitude: -1.75" or "lat=51.04 lng=-1.75"
LABELED_RE = re.compile(r"\b(lat(?:itude)?|long(?:itude)?|lon|lng)\b\s*[:=]?\s*([^,;]+)", re.IGNORECASE)

# unicode variants of degree/minute/second marks
_SYMBOL_MAP = str.maketrans({
    "\u2032": "'",   # prime
    "\u2019": "'",   # right single quote
    "\u2018": "'",   # left single quote
    "\u02b9": "'",
    "\u2033": '"',   # double prime
    "\u201c": '"',
    "\u201d": '"',
    "\u02ba": '"',
})


def _normalize(text: str) -> str:
    return text.translate(_SYMBOL_MAP).strip()


def _parse_angle(part: str, is_lat: bool) -> float:
    axis = "latitude" if is_lat else "longitude"
    allowed_hemis = "NS" if is_lat else "EW"
    part = part.strip()
    if not part:
        raise ValueError(f"Empty {axis} value")

    hemi = None
    if part[0].upper() in "NSEW":
        hemi, part = part[0].upper(), part[1:].strip()
    elif part[-1].upper() in "NSEW":
        hemi, part = part[-1].upper(), part[:-1].strip()
    if hemi and hemi not in allowed_hemis:
        raise ValueError(f"Hemisphere '{hemi}' is not valid for {axis}")

    # unify DMS/DDM/decimal into space-separated numbers
    cleaned = re.sub(r"[°'\"]", " ", part)
    tokens = cleaned.split()
    if not 1 <= len(tokens) <= 3:
        raise ValueError(f"Cannot parse {axis} from '{part}'")

    try:
        numbers = [float(t) for t in tokens]
    except ValueError:
        raise ValueError(f"Cannot parse {axis} from '{part}'") from None

    degrees, minutes, seconds = (numbers + [0.0, 0.0])[:3]
    if hemi and degrees < 0:
        raise ValueError(f"Ambiguous {axis}: both negative sign and hemisphere '{hemi}'")
    if minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
        raise ValueError(f"Minutes/seconds out of range in {axis} '{part}'")

    sign = -1.0 if degrees < 0 or hemi in ("S", "W") else 1.0
    value = sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)

    limit = 90.0 if is_lat else 180.0
    if not -limit <= value <= limit:
        raise ValueError(f"{axis.capitalize()} {value} out of range ±{limit}")
    return value


def parse_coordinate(text: str) -> tuple[float, float]:
    """Parse a coordinate string in any supported format into (lat, lon)."""
    s = _normalize(text)
    if not s:
        raise ValueError("Empty coordinate")

    labeled = LABELED_RE.findall(s)
    if labeled:
        values = {}
        for label, value in labeled:
            key = "lat" if label.lower().startswith("lat") else "lon"
            values[key] = value.strip()
        if set(values) != {"lat", "lon"}:
            raise ValueError(f"Labeled coordinate needs both latitude and longitude: '{text}'")
        return _parse_angle(values["lat"], True), _parse_angle(values["lon"], False)

    if GEOHASH_RE.fullmatch(s):
        lat, lon = pygeohash.decode(s)
        return float(lat), float(lon)

    if "," in s:
        lat_s, lon_s = s.split(",", 1)
    else:
        m = re.fullmatch(r"(.*?[NSns])\s+(.*?[EWew])", s)
        if m:
            lat_s, lon_s = m.group(1), m.group(2)
        else:
            tokens = s.split()
            if len(tokens) != 2:
                raise ValueError(f"Cannot parse coordinate '{text}'")
            lat_s, lon_s = tokens

    return _parse_angle(lat_s, True), _parse_angle(lon_s, False)


def format_distance(point1: tuple[float, float], point2: tuple[float, float]) -> str:
    d = geodesic(point1, point2)
    return (
        f"Point 1: {point1[0]:.6f}, {point1[1]:.6f}\n"
        f"Point 2: {point2[0]:.6f}, {point2[1]:.6f}\n"
        f"Distance:\n"
        f"  {d.kilometers:,.3f} km\n"
        f"  {d.meters:,.1f} m\n"
        f"  {d.miles:,.3f} mi\n"
        f"  {d.nautical:,.3f} nmi"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute the geodesic distance between two coordinates. "
        "Supports decimal degrees, DMS, degrees decimal minutes, and geohash.",
    )
    parser.add_argument("coord1", nargs="?", help='first coordinate, e.g. "48.8566, 2.3522"')
    parser.add_argument("coord2", nargs="?", help="second coordinate, e.g. \"40°26'46\\\"N 79°58'56\\\"W\"")
    args = parser.parse_args(argv)

    coord1 = args.coord1 or input("Enter first coordinate: ")
    coord2 = args.coord2 or input("Enter second coordinate: ")

    try:
        point1 = parse_coordinate(coord1)
        point2 = parse_coordinate(coord2)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_distance(point1, point2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
