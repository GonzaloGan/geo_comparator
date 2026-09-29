# Geo Comparator

Command-line tool that computes the geodesic (WGS-84) distance between two geographic coordinates, accepting several common input formats.

## Features

- Geodesic distance via [geopy](https://geopy.readthedocs.io/) (WGS-84 ellipsoid)
- Auto-detects the input format — no flags needed
- Output in kilometers, meters, miles, and nautical miles
- CLI arguments or interactive prompts
- Clear error messages and non-zero exit code on invalid input

## Supported formats

| Format | Example |
| --- | --- |
| Decimal degrees | `48.8566, 2.3522` or `40.7128 -74.0060` |
| Labeled | `Latitude: 51.0407754, Longitude: -1.7588855` |
| DMS (degrees/minutes/seconds) | `40°26'46"N 79°58'56"W` |
| Degrees decimal minutes | `40°26.767'N 79°58.933'W` |
| Geohash | `u09tvw0f` |

Labels are order-independent (`Longitude: ..., Latitude: ...` works) and accept `lat`, `latitude`, `lon`, `long`, `longitude`, `lng` with `:` or `=`.

## Requirements

- Python 3.10+
- [geopy](https://pypi.org/project/geopy/)
- [pygeohash](https://pypi.org/project/pygeohash/)

## Installation

```powershell
# recommended: use a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Usage

```powershell
# two coordinates as arguments (quote each one)
python geo_compare.py "48.8566, 2.3522" "40.7128, -74.0060"

# mixed formats
python geo_compare.py "Latitude: 51.0407754, Longitude: -1.7588855" "u09tvw0f"

# no arguments: interactive prompts
python geo_compare.py
```

Example output:

```text
Point 1: 48.856600, 2.352200
Point 2: 40.712800, -74.006000
Distance:
  5,837.413 km
  5,837,413.2 m
  3,627.183 mi
  3,152.167 nmi
```

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | Invalid or unparseable coordinate |

## Using as a library

```python
from geo_compare import parse_coordinate
from geopy.distance import geodesic

p1 = parse_coordinate("40°26'46\"N 79°58'56\"W")
p2 = parse_coordinate("48.8566, 2.3522")
print(geodesic(p1, p2).kilometers)
```

## Validation rules

- Latitude must be within ±90°, longitude within ±180°
- Minutes and seconds must be in `[0, 60)`
- A value may use a sign **or** a hemisphere letter, not both (`-40°N` is rejected as ambiguous)
- Geohashes must be 4–12 base32 characters

## Troubleshooting

- **`Import "geopy" could not be resolved`** — dependencies not installed; run `pip install -r requirements.txt` in the active environment.
- **PowerShell eats the `"` in DMS strings** — escape inner quotes with a backtick: `"40°26'46`"N 79°58'56`"W"`.
- **`Hemisphere 'E' is not valid for latitude`** — the coordinate is in lon/lat order; use labels or swap the values.
