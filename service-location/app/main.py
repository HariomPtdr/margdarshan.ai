"""service-location — reverse-geocode + pincode lookups.

Uses LocationIQ if LOCATIONIQ_API_KEY is set, otherwise falls back to
OpenStreetMap Nominatim (free, no key, but rate-limited).
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from grievance_schema import LocationData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONIQ_KEY = os.getenv("LOCATIONIQ_API_KEY", "")
PINCODE_CACHE_PATH = Path(__file__).parent / "data" / "pincode_to_ward.json"

app = FastAPI(title="service-location", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pincode_cache: dict = {}
if PINCODE_CACHE_PATH.exists():
    with open(PINCODE_CACHE_PATH) as f:
        _pincode_cache = json.load(f)
    logger.info(f"Loaded {len(_pincode_cache)} pincode entries from offline cache")


class ReverseGeocodeRequest(BaseModel):
    lat: float
    lon: float


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "location", "provider": "locationiq" if LOCATIONIQ_KEY else "osm"}


@app.post("/api/v1/reverse-geocode", response_model=LocationData)
async def reverse_geocode(req: ReverseGeocodeRequest):
    if LOCATIONIQ_KEY:
        return await _reverse_locationiq(req.lat, req.lon)
    return await _reverse_osm(req.lat, req.lon)


@app.get("/api/v1/pincode/{pincode}")
async def lookup_pincode(pincode: str):
    """Return cached admin metadata for a pincode."""
    if pincode in _pincode_cache:
        return _pincode_cache[pincode]
    return await _pincode_postoffice_api(pincode)


# ── LocationIQ (preferred, free 5k/day with key) ───────────────────────

async def _reverse_locationiq(lat: float, lon: float) -> LocationData:
    url = "https://us1.locationiq.com/v1/reverse"
    params = {"key": LOCATIONIQ_KEY, "lat": lat, "lon": lon, "format": "json", "addressdetails": 1}
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            logger.error(f"LocationIQ failed: {r.status_code} {r.text[:200]}")
            return await _reverse_osm(lat, lon)
        data = r.json()

    addr = data.get("address", {})
    return LocationData(
        lat=lat,
        lon=lon,
        pincode=addr.get("postcode", ""),
        ward=addr.get("suburb") or addr.get("neighbourhood"),
        district=addr.get("state_district") or addr.get("city_district") or addr.get("city", ""),
        state=addr.get("state", ""),
        address_text=data.get("display_name", ""),
        map_provider="locationiq",
    )


# ── OpenStreetMap Nominatim (fallback) ─────────────────────────────────

async def _reverse_osm(lat: float, lon: float) -> LocationData:
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": 1}
    headers = {"User-Agent": "shikayat-saathi/1.0"}
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(url, params=params, headers=headers)
        if r.status_code != 200:
            raise HTTPException(503, "All map providers failed")
        data = r.json()

    addr = data.get("address", {})
    return LocationData(
        lat=lat,
        lon=lon,
        pincode=addr.get("postcode", ""),
        ward=addr.get("suburb") or addr.get("neighbourhood"),
        district=addr.get("state_district") or addr.get("city_district") or addr.get("city", ""),
        state=addr.get("state", ""),
        address_text=data.get("display_name", ""),
        map_provider="osm",
    )


# ── India Post pincode API (no key, free) ──────────────────────────────

async def _pincode_postoffice_api(pincode: str) -> dict:
    url = f"https://api.postalpincode.in/pincode/{pincode}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(url)
        if r.status_code != 200:
            raise HTTPException(404, "Pincode not found")
        data = r.json()

    if not data or data[0].get("Status") != "Success":
        raise HTTPException(404, "Pincode not found")

    offices = data[0].get("PostOffice") or []
    if not offices:
        raise HTTPException(404, "Pincode has no offices")

    first = offices[0]
    return {
        "pincode": pincode,
        "district": first.get("District", ""),
        "state": first.get("State", ""),
        "office_name": first.get("Name", ""),
        "block": first.get("Block", ""),
    }
