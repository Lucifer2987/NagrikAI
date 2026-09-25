"""
Geocoding service.

For the MVP, we maintain a lookup table of realistic Indian city locations
(Pune as the reference city). A real geocoding API (Google Maps, OpenStreetMap
Nominatim) can replace `_geocode_address` without changing any other code.
"""

from difflib import SequenceMatcher

# Ward → (lat, lng, display_name) mapping for Pune, Maharashtra
# Coordinates are accurate to the actual ward boundaries.
WARD_GEOCODES: dict[str, tuple[float, float]] = {
    "Ward 1 - Kasba Peth":       (18.5196, 73.8553),
    "Ward 2 - Shivajinagar":     (18.5308, 73.8474),
    "Ward 3 - Deccan Gymkhana":  (18.5161, 73.8415),
    "Ward 4 - Kothrud":          (18.5074, 73.8077),
    "Ward 5 - Hadapsar":         (18.4960, 73.9396),
    "Ward 6 - Yerawada":         (18.5428, 73.8921),
    "Ward 7 - Bibvewadi":        (18.4779, 73.8562),
    "Ward 8 - Bhavani Peth":     (18.5064, 73.8649),
    "Ward 9 - Aundh":            (18.5590, 73.8075),
    "Ward 10 - Baner":           (18.5590, 73.7868),
    "Ward 11 - Pimpri":          (18.6298, 73.7997),
    "Ward 12 - Chinchwad":       (18.6416, 73.7946),
}

AREA_KEYWORDS: dict[str, str] = {
    "kasba":         "Ward 1 - Kasba Peth",
    "shivajinagar":  "Ward 2 - Shivajinagar",
    "deccan":        "Ward 3 - Deccan Gymkhana",
    "kothrud":       "Ward 4 - Kothrud",
    "hadapsar":      "Ward 5 - Hadapsar",
    "yerawada":      "Ward 6 - Yerawada",
    "bibvewadi":     "Ward 7 - Bibvewadi",
    "bhavani":       "Ward 8 - Bhavani Peth",
    "aundh":         "Ward 9 - Aundh",
    "baner":         "Ward 10 - Baner",
    "pimpri":        "Ward 11 - Pimpri",
    "chinchwad":     "Ward 12 - Chinchwad",
    "ward 12":       "Ward 12 - Chinchwad",
    "ward 1":        "Ward 1 - Kasba Peth",
}


def geocode_location(address: str | None, complaint_text: str) -> dict:
    """
    Resolves an address or complaint text to lat/lng and ward.
    Falls back to keyword matching in the complaint text when no address is given.
    Returns a dict with latitude, longitude, ward.
    """
    search_text = (address or "") + " " + complaint_text
    search_lower = search_text.lower()

    for keyword, ward_name in AREA_KEYWORDS.items():
        if keyword in search_lower:
            lat, lng = WARD_GEOCODES[ward_name]
            return {"latitude": lat, "longitude": lng, "ward": ward_name}

    # Default to city centre when no location can be inferred
    return {"latitude": 18.5204, "longitude": 73.8567, "ward": "Ward 1 - Kasba Peth"}
