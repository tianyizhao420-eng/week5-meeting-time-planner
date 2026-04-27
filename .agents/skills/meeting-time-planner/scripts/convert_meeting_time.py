#!/usr/bin/env python3
"""
convert_meeting_time.py

Deterministic core of the meeting-time-planner skill.

Given a proposed meeting datetime (in a source city/timezone) and a list of
target cities, this script:
  1. Converts the meeting time to each target city's local time
  2. Determines whether that local time falls within working hours (Mon–Fri 09:00–18:00)
  3. Checks whether that date is a public holiday in the relevant country

Output: JSON array, one object per city, printed to stdout.
Errors: human-readable message on stderr, exit code 1.

Usage:
  python convert_meeting_time.py --time "2025-06-10 14:00" \
                                 --source "New York" \
                                 --cities "London,Tokyo,Sydney,Beijing"
"""

import argparse
import json
import sys
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Tuple

try:
    import pytz
except ImportError:
    print(
        "ERROR: 'pytz' is not installed. Run: pip install pytz",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import holidays as hol_lib
except ImportError:
    print(
        "ERROR: 'holidays' is not installed. Run: pip install holidays",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# City → (IANA timezone, ISO-3166-1 alpha-2 country code, subdivision or None)
# ---------------------------------------------------------------------------
CITY_DB: Dict[str, Tuple[str, str, Optional[str]]] = {
    # North America
    "new york":        ("America/New_York",     "US", "NY"),
    "new york city":   ("America/New_York",     "US", "NY"),
    "nyc":             ("America/New_York",     "US", "NY"),
    "boston":          ("America/New_York",     "US", "MA"),
    "washington":      ("America/New_York",     "US", "DC"),
    "washington dc":   ("America/New_York",     "US", "DC"),
    "miami":           ("America/New_York",     "US", "FL"),
    "atlanta":         ("America/New_York",     "US", "GA"),
    "chicago":         ("America/Chicago",      "US", "IL"),
    "houston":         ("America/Chicago",      "US", "TX"),
    "dallas":          ("America/Chicago",      "US", "TX"),
    "denver":          ("America/Denver",       "US", "CO"),
    "phoenix":         ("America/Phoenix",      "US", "AZ"),
    "los angeles":     ("America/Los_Angeles",  "US", "CA"),
    "la":              ("America/Los_Angeles",  "US", "CA"),
    "san francisco":   ("America/Los_Angeles",  "US", "CA"),
    "sf":              ("America/Los_Angeles",  "US", "CA"),
    "seattle":         ("America/Los_Angeles",  "US", "WA"),
    "toronto":         ("America/Toronto",      "CA", "ON"),
    "montreal":        ("America/Toronto",      "CA", "QC"),
    "vancouver":       ("America/Vancouver",    "CA", "BC"),
    "mexico city":     ("America/Mexico_City",  "MX", None),
    "sao paulo":       ("America/Sao_Paulo",    "BR", None),
    "são paulo":       ("America/Sao_Paulo",    "BR", None),
    "buenos aires":    ("America/Argentina/Buenos_Aires", "AR", None),
    "santiago":        ("America/Santiago",     "CL", None),
    "bogota":          ("America/Bogota",       "CO", None),
    # Europe
    "london":          ("Europe/London",        "GB", None),
    "dublin":          ("Europe/Dublin",        "IE", None),
    "lisbon":          ("Europe/Lisbon",        "PT", None),
    "madrid":          ("Europe/Madrid",        "ES", None),
    "paris":           ("Europe/Paris",         "FR", None),
    "amsterdam":       ("Europe/Amsterdam",     "NL", None),
    "brussels":        ("Europe/Brussels",      "BE", None),
    "berlin":          ("Europe/Berlin",        "DE", None),
    "frankfurt":       ("Europe/Berlin",        "DE", None),
    "munich":          ("Europe/Berlin",        "DE", None),
    "zurich":          ("Europe/Zurich",        "CH", None),
    "geneva":          ("Europe/Zurich",        "CH", None),
    "rome":            ("Europe/Rome",          "IT", None),
    "milan":           ("Europe/Rome",          "IT", None),
    "vienna":          ("Europe/Vienna",        "AT", None),
    "prague":          ("Europe/Prague",        "CZ", None),
    "warsaw":          ("Europe/Warsaw",        "PL", None),
    "stockholm":       ("Europe/Stockholm",     "SE", None),
    "oslo":            ("Europe/Oslo",          "NO", None),
    "copenhagen":      ("Europe/Copenhagen",    "DK", None),
    "helsinki":        ("Europe/Helsinki",      "FI", None),
    "athens":          ("Europe/Athens",        "GR", None),
    "istanbul":        ("Europe/Istanbul",      "TR", None),
    "moscow":          ("Europe/Moscow",        "RU", None),
    "kyiv":            ("Europe/Kyiv",          "UA", None),
    # Middle East & Africa
    "dubai":           ("Asia/Dubai",           "AE", None),
    "abu dhabi":       ("Asia/Dubai",           "AE", None),
    "riyadh":          ("Asia/Riyadh",          "SA", None),
    "tel aviv":        ("Asia/Jerusalem",       "IL", None),
    "jerusalem":       ("Asia/Jerusalem",       "IL", None),
    "cairo":           ("Africa/Cairo",         "EG", None),
    "nairobi":         ("Africa/Nairobi",       "KE", None),
    "johannesburg":    ("Africa/Johannesburg",  "ZA", None),
    "cape town":       ("Africa/Johannesburg",  "ZA", None),
    "lagos":           ("Africa/Lagos",         "NG", None),
    "accra":           ("Africa/Accra",         "GH", None),
    # South & Southeast Asia
    "mumbai":          ("Asia/Kolkata",         "IN", None),
    "delhi":           ("Asia/Kolkata",         "IN", None),
    "new delhi":       ("Asia/Kolkata",         "IN", None),
    "bangalore":       ("Asia/Kolkata",         "IN", None),
    "hyderabad":       ("Asia/Kolkata",         "IN", None),
    "kolkata":         ("Asia/Kolkata",         "IN", None),
    "karachi":         ("Asia/Karachi",         "PK", None),
    "lahore":          ("Asia/Karachi",         "PK", None),
    "dhaka":           ("Asia/Dhaka",           "BD", None),
    "colombo":         ("Asia/Colombo",         "LK", None),
    "kathmandu":       ("Asia/Kathmandu",       "NP", None),
    "bangkok":         ("Asia/Bangkok",         "TH", None),
    "ho chi minh":     ("Asia/Ho_Chi_Minh",     "VN", None),
    "hanoi":           ("Asia/Bangkok",         "VN", None),
    "jakarta":         ("Asia/Jakarta",         "ID", None),
    "kuala lumpur":    ("Asia/Kuala_Lumpur",    "MY", None),
    "singapore":       ("Asia/Singapore",       "SG", None),
    "manila":          ("Asia/Manila",          "PH", None),
    # East Asia
    "beijing":         ("Asia/Shanghai",        "CN", None),
    "shanghai":        ("Asia/Shanghai",        "CN", None),
    "guangzhou":       ("Asia/Shanghai",        "CN", None),
    "shenzhen":        ("Asia/Shanghai",        "CN", None),
    "hong kong":       ("Asia/Hong_Kong",       "HK", None),
    "hk":              ("Asia/Hong_Kong",       "HK", None),
    "taipei":          ("Asia/Taipei",          "TW", None),
    "seoul":           ("Asia/Seoul",           "KR", None),
    "tokyo":           ("Asia/Tokyo",           "JP", None),
    "osaka":           ("Asia/Tokyo",           "JP", None),
    # Oceania
    "sydney":          ("Australia/Sydney",     "AU", "NSW"),
    "melbourne":       ("Australia/Melbourne",  "AU", "VIC"),
    "brisbane":        ("Australia/Brisbane",   "AU", "QLD"),
    "perth":           ("Australia/Perth",      "AU", "WA"),
    "auckland":        ("Pacific/Auckland",     "NZ", None),
    "wellington":      ("Pacific/Auckland",     "NZ", None),
    "honolulu":        ("Pacific/Honolulu",     "US", "HI"),
}

WORK_START = dt_time(9, 0)
WORK_END   = dt_time(18, 0)
WORKDAYS   = {0, 1, 2, 3, 4}  # Mon–Fri


def resolve_city(name: str) -> Tuple[str, str, Optional[str], str]:
    """Return (iana_tz, country, subdivision, canonical_name) or raise ValueError."""
    key = name.strip().lower()
    if key in CITY_DB:
        tz, country, sub = CITY_DB[key]
        return tz, country, sub, name.strip().title()

    # Check if the user passed an IANA timezone string directly
    try:
        pytz.timezone(name.strip())
        return name.strip(), "XX", None, name.strip()
    except pytz.UnknownTimeZoneError:
        pass

    # Fuzzy partial match (first match wins)
    for db_key, (tz, country, sub) in CITY_DB.items():
        if key in db_key or db_key in key:
            return tz, country, sub, db_key.title()

    supported = ", ".join(sorted({k.title() for k in CITY_DB}))
    raise ValueError(
        "Unknown city: '{}'. Supported cities include: {}.\n"
        "You may also pass an IANA timezone string such as 'America/New_York'.".format(name, supported)
    )


def is_working_hours(local_dt: datetime) -> Tuple[bool, str]:
    """Return (is_work, reason_string)."""
    weekday = local_dt.weekday()
    t = local_dt.time()
    if weekday not in WORKDAYS:
        day_name = local_dt.strftime("%A")
        return False, f"Weekend ({day_name})"
    if t < WORK_START:
        return False, f"Before 09:00 ({t.strftime('%H:%M')})"
    if t >= WORK_END:
        return False, f"After 18:00 ({t.strftime('%H:%M')})"
    return True, "Within 09:00–18:00"


def check_holiday(local_dt: datetime, country: str, subdivision: Optional[str]) -> Tuple[bool, str]:
    """Return (is_holiday, holiday_name_or_empty)."""
    if country == "XX":
        return False, ""
    try:
        if subdivision:
            country_hols = hol_lib.country_holidays(country, subdiv=subdivision, years=local_dt.year)
        else:
            country_hols = hol_lib.country_holidays(country, years=local_dt.year)
        date_key = local_dt.date()
        if date_key in country_hols:
            return True, country_hols[date_key]
        return False, ""
    except Exception:
        return False, ""


def convert(meeting_time_str: str, source: str, targets: List[str]) -> List[dict]:
    # Resolve source
    src_tz_name, _, _, src_label = resolve_city(source)
    src_tz = pytz.timezone(src_tz_name)

    # Parse naive datetime then localize
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y/%m/%d %H:%M",
                "%m/%d/%Y %H:%M", "%d-%m-%Y %H:%M"):
        try:
            naive_dt = datetime.strptime(meeting_time_str.strip(), fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError(
            f"Cannot parse meeting time '{meeting_time_str}'. "
            "Expected format: YYYY-MM-DD HH:MM (e.g. 2025-06-10 14:00)"
        )

    src_dt = src_tz.localize(naive_dt)

    results = []
    for city_name in targets:
        city_name = city_name.strip()
        if not city_name:
            continue
        try:
            tgt_tz_name, country, subdivision, canonical = resolve_city(city_name)
        except ValueError as exc:
            results.append({"city": city_name, "error": str(exc)})
            continue

        tgt_tz = pytz.timezone(tgt_tz_name)
        local_dt = src_dt.astimezone(tgt_tz)

        is_work, work_reason = is_working_hours(local_dt)
        is_holiday, holiday_name = check_holiday(local_dt, country, subdivision)

        results.append({
            "city":          canonical,
            "timezone":      tgt_tz_name,
            "local_time":    local_dt.strftime("%Y-%m-%d %H:%M"),
            "day_of_week":   local_dt.strftime("%A"),
            "working_hours": is_work,
            "work_reason":   work_reason,
            "holiday":       is_holiday,
            "holiday_name":  holiday_name,
            "utc_offset":    local_dt.strftime("%z"),
        })

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a meeting time across timezones and check working hours / holidays."
    )
    parser.add_argument("--time",   required=True, help="Meeting datetime, e.g. '2025-06-10 14:00'")
    parser.add_argument("--source", required=True, help="Source city or IANA timezone")
    parser.add_argument("--cities", required=True, help="Comma-separated target cities")
    args = parser.parse_args()

    target_list = [c.strip() for c in args.cities.split(",") if c.strip()]
    if not target_list:
        print("ERROR: --cities must contain at least one city name.", file=sys.stderr)
        sys.exit(1)

    try:
        results = convert(args.time, args.source, target_list)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
