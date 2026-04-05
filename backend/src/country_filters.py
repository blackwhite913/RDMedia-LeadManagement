"""
Normalize messy `Lead.country` strings for export filters.

- Drops junk like numeric-only codes (e.g. "314" stored as text).
- Maps free text to canonical country names via country_converter ISO3.
- Excludes regions/cities that do not resolve to a valid ISO 3166-1 alpha-3 code.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import country_converter as coco

_ISO3 = re.compile(r"^[A-Z]{3}$")

# Stable UI ordering for continent groups (country_converter uses "America" for the Americas)
_CONTINENT_ORDER = [
    "Africa",
    "America",
    "Asia",
    "Europe",
    "Oceania",
    "Antarctica",
]


def _canonical_name_and_continent(raw: str) -> Optional[Tuple[str, str]]:
    s = (raw or "").strip()
    if len(s) < 2:
        return None
    # Reject numeric-only values (bad imports / IDs like "314")
    if re.fullmatch(r"\d+", s):
        return None

    cc = coco.CountryConverter()
    iso3 = cc.convert(s, to="ISO3", not_found=None)
    if not isinstance(iso3, str) or not _ISO3.match(iso3):
        return None

    name = cc.convert(iso3, to="name_short")
    continent = cc.convert(iso3, to="continent")
    if not isinstance(name, str) or not isinstance(continent, str):
        return None
    return (name, continent)


def normalize_country_options(distinct_raw: List[str]) -> List[Dict[str, str]]:
    """
    Deduplicate by canonical country name; sort by continent then name.
    """
    by_name: Dict[str, str] = {}
    for raw in distinct_raw:
        pair = _canonical_name_and_continent(raw)
        if not pair:
            continue
        name, continent = pair
        by_name[name] = continent

    def sort_key(item: Tuple[str, str]) -> Tuple[int, str]:
        name, cont = item
        try:
            idx = _CONTINENT_ORDER.index(cont)
        except ValueError:
            idx = 99
        return (idx, name.lower())

    items = sorted(by_name.items(), key=sort_key)
    return [{"name": n, "continent": c} for n, c in items]
