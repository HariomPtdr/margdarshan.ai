# service-location

Map reverse-geocoding + pincode lookup. Replaces text-based location extraction.

## Endpoints

```
POST /api/v1/reverse-geocode  body: {lat, lon}    → LocationData
GET  /api/v1/pincode/{pin}                         → admin metadata
GET  /healthz
```

## Providers

- Primary: **Mappls** (formerly MapmyIndia) — best Indian admin boundaries
- Fallback: **OpenStreetMap Nominatim** — free, no key
- Pincode lookup: **India Post API** (api.postalpincode.in) — free, no key

If `MAPPLS_API_KEY` is unset, the service uses OSM.

## Offline cache

`app/data/pincode_to_ward.json` ships with a few MP pincodes for demo. In prod, replace with the full India pincode dump (~1.5L entries).
