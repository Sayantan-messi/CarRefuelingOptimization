import requests
from django.core.cache import cache


class ProviderError(Exception):
    pass


USER_AGENT = "car-fueling-optimization/1.0"


def _get(url, params=None):
    try:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=(5, 30),
        )

        if response.status_code >= 400:
            raise ProviderError(
                f"Provider returned HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        return response.json()

    except requests.RequestException as exc:
        raise ProviderError(
            "Routing/geocoding provider unavailable."
        ) from exc


def search(text, station=False):
    """
    Geocode using Nominatim.
    Returns GeoJSON-like structure compatible
    with the rest of the existing code.
    """

    cache_key = f"geocode:{text}"

    cached = cache.get(cache_key)

    if cached:
        return cached

    data = _get(
        "https://nominatim.openstreetmap.org/search",
        {
            "q": text,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "us",
        },
    )

    if not data:
        raise ProviderError(f"No location found for: {text}")

    result = {
        "geometry": {
            "coordinates": [
                float(data[0]["lon"]),
                float(data[0]["lat"]),
            ]
        },
        "properties": {
            "country_a": "USA"
        },
    }

    cache.set(cache_key, result, 86400)

    return result


def route(points):
    """
    Route using public OSRM.
    Supports existing service.py
    without modification.
    """

    if len(points) < 2:
        raise ProviderError("Route requires at least two points")

    coords = ";".join(
        f"{lon},{lat}"
        for lon, lat in points
    )

    data = _get(
        f"https://router.project-osrm.org/route/v1/driving/{coords}",
        {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        },
    )

    routes = data.get("routes", [])

    if not routes:
        raise ProviderError("No drivable route found")

    route_data = routes[0]

    geometry = route_data["geometry"]

    total_distance = route_data["distance"]

    segments = []

    if len(points) == 2:
        segments.append(
            {
                "distance": total_distance
            }
        )
    else:
        #
        # Approximate segment breakdown
        # for compatibility with existing code.
        #
        per_segment = total_distance / (len(points) - 1)

        for _ in range(len(points) - 1):
            segments.append(
                {
                    "distance": per_segment
                }
            )

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "summary": {
                "distance": total_distance
            },
            "segments": segments,
        },
    }