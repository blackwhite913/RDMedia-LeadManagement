"""Location parsing helpers for ingestion and data cleanup."""
import re
from typing import Optional


COUNTRY_KEYWORDS = {
    "united states": "United States",
    "usa": "United States",
    "u.s.a": "United States",
    "us": "United States",
    "united kingdom": "United Kingdom",
    "uk": "United Kingdom",
    "england": "United Kingdom",
    "canada": "Canada",
    "mexico": "Mexico",
    "australia": "Australia",
    "new zealand": "New Zealand",
    "germany": "Germany",
    "france": "France",
    "spain": "Spain",
    "italy": "Italy",
    "netherlands": "Netherlands",
    "sweden": "Sweden",
    "norway": "Norway",
    "denmark": "Denmark",
    "finland": "Finland",
    "ireland": "Ireland",
    "poland": "Poland",
    "portugal": "Portugal",
    "switzerland": "Switzerland",
    "austria": "Austria",
    "belgium": "Belgium",
    "india": "India",
    "pakistan": "Pakistan",
    "bangladesh": "Bangladesh",
    "singapore": "Singapore",
    "malaysia": "Malaysia",
    "indonesia": "Indonesia",
    "philippines": "Philippines",
    "japan": "Japan",
    "south korea": "South Korea",
    "korea": "South Korea",
    "china": "China",
    "hong kong": "Hong Kong",
    "taiwan": "Taiwan",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "saudi arabia": "Saudi Arabia",
    "qatar": "Qatar",
    "egypt": "Egypt",
    "nigeria": "Nigeria",
    "south africa": "South Africa",
    "kenya": "Kenya",
    "brazil": "Brazil",
    "argentina": "Argentina",
    "chile": "Chile",
    "colombia": "Colombia",
}

CITY_TO_COUNTRY = {
    "new york": "United States",
    "los angeles": "United States",
    "san francisco": "United States",
    "chicago": "United States",
    "london": "United Kingdom",
    "manchester": "United Kingdom",
    "toronto": "Canada",
    "vancouver": "Canada",
    "berlin": "Germany",
    "munich": "Germany",
    "paris": "France",
    "madrid": "Spain",
    "barcelona": "Spain",
    "rome": "Italy",
    "milan": "Italy",
    "amsterdam": "Netherlands",
    "dublin": "Ireland",
    "zurich": "Switzerland",
    "stockholm": "Sweden",
    "oslo": "Norway",
    "helsinki": "Finland",
    "warsaw": "Poland",
    "lisbon": "Portugal",
    "vienna": "Austria",
    "tokyo": "Japan",
    "osaka": "Japan",
    "seoul": "South Korea",
    "beijing": "China",
    "shanghai": "China",
    "singapore": "Singapore",
    "sydney": "Australia",
    "melbourne": "Australia",
    "auckland": "New Zealand",
    "dubai": "United Arab Emirates",
    "doha": "Qatar",
    "riyadh": "Saudi Arabia",
    "cairo": "Egypt",
    "lagos": "Nigeria",
    "johannesburg": "South Africa",
    "nairobi": "Kenya",
    "mumbai": "India",
    "delhi": "India",
    "bengaluru": "India",
    "karachi": "Pakistan",
    "lahore": "Pakistan",
    "sao paulo": "Brazil",
    "buenos aires": "Argentina",
    "santiago": "Chile",
    "bogota": "Colombia",
}


def _contains_keyword(text: str, keyword: str) -> bool:
    """Match short tokens by word boundary to avoid false positives."""
    if len(keyword) <= 3 and keyword.isalpha():
        pattern = r"\b" + re.escape(keyword) + r"\b"
        return re.search(pattern, text) is not None
    return keyword in text


def _normalize_country_token(token: str) -> Optional[str]:
    """Try to normalize one address fragment into a canonical country."""
    if not token:
        return None

    normalized = token.strip().lower()
    if not normalized:
        return None
    if normalized.isdigit():
        return None

    for keyword, canonical in COUNTRY_KEYWORDS.items():
        if _contains_keyword(normalized, keyword):
            return canonical

    # Reasonable fallback for already-country-like fragments.
    if len(normalized) > 1 and not re.search(r"\d", normalized):
        return token.strip()

    return None


def extract_country(address: str) -> Optional[str]:
    """
    Extract a country from free-form address text.

    Strategy:
    1) Keyword detection across the entire address string.
    2) Fallback to comma-separated fragments (second-to-last, then last).
    """
    if not address or not isinstance(address, str):
        return None

    raw = address.strip()
    if not raw:
        return None

    lowered = raw.lower()
    for keyword, canonical in COUNTRY_KEYWORDS.items():
        if _contains_keyword(lowered, keyword):
            return canonical

    parts = [part.strip() for part in raw.split(",") if part and part.strip()]
    if len(parts) >= 2:
        from_second_last = _normalize_country_token(parts[-2])
        if from_second_last:
            return from_second_last

    if parts:
        from_last = _normalize_country_token(parts[-1])
        if from_last:
            return from_last

    return None


def infer_country_from_city(city: str) -> Optional[str]:
    """Infer country from city when no address is available."""
    if not city or not isinstance(city, str):
        return None

    city_key = city.strip().lower()
    if not city_key:
        return None

    return CITY_TO_COUNTRY.get(city_key)

