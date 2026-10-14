"""Location helpers backed by OpenStreetMap.

* Nominatim turns "Gandhipuram, Coimbatore" into coordinates and coordinates
  from the browser into locality / district / state / PIN code.
* Overpass lists police stations (amenity=police) and courts
  (amenity=courthouse) around a point.

Both services are free and rate limited, so requests carry an identifying
User-Agent, results are cached in-process, and failures return nothing rather
than raising: the filing flow works without nearby results.
"""

from __future__ import annotations

import logging
import math
import os
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)

NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org").rstrip("/")
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
USER_AGENT = os.getenv("GEO_USER_AGENT", "ChatLaw/1.0 (legal information service; +https://chatlaw.in)")
TIMEOUT_SECONDS = float(os.getenv("GEO_TIMEOUT_SECONDS", "12"))
_CACHE_TTL_SECONDS = 24 * 3600
_cache: dict[tuple, tuple[float, Any]] = {}
_lock = threading.Lock()
_last_nominatim = [0.0]

HttpGet = Callable[[str, dict[str, Any]], Any]


@dataclass(frozen=True)
class Place:
    latitude: float
    longitude: float
    display_name: str
    locality: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = None
    country: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NearbyOffice:
    id: str
    name: str
    latitude: float
    longitude: float
    distance_km: float
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    kind_hint: str | None = None  # e.g. "women police station", "family court"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def _cached(key: tuple, producer: Callable[[], Any]) -> Any:
    now = time.time()
    with _lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < _CACHE_TTL_SECONDS:
            return hit[1]
    value = producer()
    if value is not None:
        with _lock:
            if len(_cache) > 2048:
                _cache.clear()
            _cache[key] = (now, value)
    return value


def _default_get(url: str, params: dict[str, Any]) -> Any:
    import httpx

    response = httpx.get(url, params=params, timeout=TIMEOUT_SECONDS,
                         headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
    response.raise_for_status()
    return response.json()


def _nominatim_throttle() -> None:
    # Nominatim's usage policy allows one request per second.
    with _lock:
        wait = 1.0 - (time.monotonic() - _last_nominatim[0])
        if wait > 0:
            time.sleep(wait)
        _last_nominatim[0] = time.monotonic()


def _place_from(item: dict[str, Any]) -> Place | None:
    try:
        lat, lon = float(item["lat"]), float(item["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    address = item.get("address") or {}
    city = address.get("city") or address.get("town") or address.get("village") or address.get("municipality")
    district = address.get("state_district") or address.get("county") or address.get("district")
    if district:
        district = district.replace(" District", "").replace(" district", "").strip()
    locality = address.get("suburb") or address.get("neighbourhood") or address.get("quarter") or city
    return Place(lat, lon, item.get("display_name", ""), locality, city, district,
                 address.get("state"), address.get("postcode"), address.get("country"))


def geocode(query: str, *, http_get: HttpGet | None = None) -> Place | None:
    query = " ".join((query or "").split())
    if len(query) < 2:
        return None
    if "india" not in query.lower():
        query = f"{query}, India"
    getter = http_get or _default_get

    def produce() -> Place | None:
        try:
            _nominatim_throttle()
            data = getter(f"{NOMINATIM_URL}/search", {"q": query, "format": "jsonv2", "addressdetails": 1,
                                                     "limit": 1, "countrycodes": "in"})
        except Exception:
            logger.warning("[GEO] geocode failed for %r", query, exc_info=True)
            return None
        return _place_from(data[0]) if isinstance(data, list) and data else None

    return _cached(("geocode", query.lower()), produce)


def reverse_geocode(latitude: float, longitude: float, *, http_get: HttpGet | None = None) -> Place | None:
    getter = http_get or _default_get
    key = ("reverse", round(latitude, 3), round(longitude, 3))

    def produce() -> Place | None:
        try:
            _nominatim_throttle()
            data = getter(f"{NOMINATIM_URL}/reverse", {"lat": latitude, "lon": longitude, "format": "jsonv2",
                                                      "addressdetails": 1, "zoom": 16})
        except Exception:
            logger.warning("[GEO] reverse geocode failed", exc_info=True)
            return None
        return _place_from(data) if isinstance(data, dict) else None

    return _cached(key, produce)


def _overpass_query(amenity: str, latitude: float, longitude: float, radius_m: int) -> str:
    return (f"[out:json][timeout:20];"
            f"(node[\"amenity\"=\"{amenity}\"](around:{radius_m},{latitude},{longitude});"
            f"way[\"amenity\"=\"{amenity}\"](around:{radius_m},{latitude},{longitude});"
            f"relation[\"amenity\"=\"{amenity}\"](around:{radius_m},{latitude},{longitude}););"
            f"out center tags 60;")


def _address(tags: dict[str, str]) -> str | None:
    if tags.get("addr:full"):
        return tags["addr:full"]
    parts = [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:suburb"),
             tags.get("addr:city"), tags.get("addr:postcode")]
    text = ", ".join(p for p in parts if p)
    return text or None


def _hint(amenity: str, name: str) -> str | None:
    lowered = name.lower()
    if amenity == "police":
        if "women" in lowered or "mahila" in lowered or "awps" in lowered:
            return "women police station"
        if "traffic" in lowered:
            return "traffic police"
        return "police outpost" if "outpost" in lowered else None
    return next((label for word, label in (("family", "family court"), ("consumer", "consumer commission"),
                                           ("magistrate", "magistrate court"), ("munsif", "civil court"),
                                           ("district", "district court"), ("high court", "high court"),
                                           ("sessions", "sessions court"), ("civil", "civil court"))
                 if word in lowered), None)


def _office(amenity: str, latitude: float, longitude: float, *, oid: str, name: str, lat: float, lon: float,
            tags: dict[str, Any]) -> NearbyOffice:
    return NearbyOffice(
        id=oid, name=name, latitude=lat, longitude=lon,
        distance_km=round(haversine_km(latitude, longitude, lat, lon), 2),
        address=_address(tags), phone=tags.get("phone") or tags.get("contact:phone"),
        email=tags.get("email") or tags.get("contact:email"),
        website=tags.get("website") or tags.get("contact:website"), kind_hint=_hint(amenity, name),
    )


def _from_overpass(amenity: str, latitude: float, longitude: float, radius_m: int,
                   getter: HttpGet) -> list[NearbyOffice]:
    data = getter(OVERPASS_URL, {"data": _overpass_query(amenity, latitude, longitude, radius_m)})
    offices = []
    for element in (data or {}).get("elements", []):
        tags = element.get("tags") or {}
        name = tags.get("name:en") or tags.get("name") or tags.get("official_name")
        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if name and lat is not None and lon is not None:
            offices.append(_office(amenity, latitude, longitude, oid=f"osm-{element.get('type', 'node')}-{element.get('id')}",
                                   name=name, lat=float(lat), lon=float(lon), tags=tags))
    return offices


def _from_nominatim(amenity: str, latitude: float, longitude: float, radius_m: int,
                    getter: HttpGet) -> list[NearbyOffice]:
    """Nominatim's amenity search inside a bounding box — used when Overpass is down or busy."""
    dlat = radius_m / 111_000
    dlon = radius_m / (111_000 * max(0.2, math.cos(math.radians(latitude))))
    _nominatim_throttle()
    data = getter(f"{NOMINATIM_URL}/search", {
        "q": "police" if amenity == "police" else "courthouse", "format": "jsonv2", "limit": 40, "bounded": 1,
        "viewbox": f"{longitude - dlon},{latitude + dlat},{longitude + dlon},{latitude - dlat}",
        "extratags": 1, "addressdetails": 1, "countrycodes": "in",
    })
    offices = []
    for item in data if isinstance(data, list) else []:
        if item.get("category") != "amenity" or item.get("type") != amenity:
            continue
        name = item.get("name") or (item.get("display_name") or "").split(",")[0]
        try:
            lat, lon = float(item["lat"]), float(item["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        address = item.get("address") or {}
        tags = {**(item.get("extratags") or {}),
                "addr:street": address.get("road"), "addr:suburb": address.get("suburb"),
                "addr:city": address.get("city") or address.get("town"), "addr:postcode": address.get("postcode")}
        if name:
            offices.append(_office(amenity, latitude, longitude, oid=f"osm-{item.get('osm_type', 'node')}-{item.get('osm_id')}",
                                   name=name, lat=lat, lon=lon, tags={k: v for k, v in tags.items() if v}))
    return offices


def nearby(amenity: str, latitude: float, longitude: float, *, radius_km: float = 10.0, limit: int = 8,
           http_get: HttpGet | None = None) -> list[NearbyOffice]:
    """Police stations ("police") or courts ("courthouse") near a point, nearest first.

    Overpass is asked first (it returns every mapped office in the radius); when
    it is overloaded — which happens often — Nominatim's amenity search is used.
    """
    if amenity not in {"police", "courthouse"}:
        raise ValueError("unsupported amenity")
    radius_m = int(max(1.0, min(radius_km, 50.0)) * 1000)
    getter = http_get or _default_get
    key = ("nearby", amenity, round(latitude, 3), round(longitude, 3), radius_m)

    def produce() -> list[NearbyOffice] | None:
        found: list[NearbyOffice] | None = None
        for source in (_from_overpass, _from_nominatim):
            try:
                found = source(amenity, latitude, longitude, radius_m, getter)
            except Exception:
                logger.warning("[GEO] %s failed", source.__name__, exc_info=True)
                continue
            if found:
                break
        if found is None:
            return None
        offices: list[NearbyOffice] = []
        seen: set[str] = set()
        for office in sorted(found, key=lambda o: o.distance_km):
            dedupe = office.name.lower().strip()
            if dedupe in seen or office.distance_km > radius_m / 1000:
                continue
            seen.add(dedupe)
            offices.append(office)
        # Traffic police posts cannot register FIRs; keep them last.
        offices.sort(key=lambda o: (o.kind_hint == "traffic police", o.distance_km))
        return offices

    return (_cached(key, produce) or [])[:limit]
