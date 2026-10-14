# Django fuel route API

Prototype, not a production navigation or live-price service.

## Setup (Python 3.11+)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set your openrouteservice API key in .env.
python manage.py migrate
python manage.py import_prices data/fuel-prices-for-be-assessment.csv
```

Create a free openrouteservice account/key: https://openrouteservice.org/
Hosted limits: https://openrouteservice.org/restrictions/
Account quotas: check your dashboard; this project does not bypass quotas.

## Required coordinate enrichment

The supplied CSV has no coordinates. Do NOT use city centroids as station coordinates.

```bash
python manage.py geocode_stations suggestions.csv --limit 100 --state TX
```

Review each suggestion against the station's name, city, state, and actual road access.
Correct longitude/latitude and set verified=true only for confirmed USA stations.
Then:

```bash
python manage.py import_coordinates suggestions.csv
```

You can also supply coordinates from another legitimate station dataset in a CSV
with headers opis_id,longitude,latitude,verified. Set verified=true only after review.
Import sufficient stations for the intended routes. The API returns 422 when the
available verified stations do not support a feasible plan. This is NOT proof that
no real-world route exists. Geocoding suggestions are not guaranteed matches.
Repeat enrichment in quota-sized batches. Already verified stations are skipped.

```bash
python manage.py test
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the interactive map.

## API

```bash
curl -X POST http://127.0.0.1:8000/api/route/ \
 -H 'Content-Type: application/json' \
 -d '{"start":"Dallas, TX","finish":"Los Angeles, CA","initial_fuel_gallons":50,"reserve_gallons":2,"corridor_miles":2}'
```

Response includes route_geojson, fuel_stops, distance_miles, fuel_consumed_gallons,
fuel_purchased_gallons, total_fuel_cost_usd, remaining_fuel_gallons, assumptions,
and warnings. GeoJSON can be rendered by any compatible client. The bundled map
calls this endpoint and displays stop purchases and the total.

## Algorithm and limitations

1. Geocode USA endpoints and request a driving route, avoiding borders/ferries.
2. Project verified stations onto a narrow baseline-route corridor. These are
   approximate candidate positions, not road-access distances.
3. Apply the fixed-route greedy fuel algorithm: buy only enough to reach the
   first cheaper reachable station; otherwise fill up, capped by fuel needed to
   finish. Already-owned initial fuel is carried forward correctly.
4. Route through the selected stations. Recompute fuel purchases using actual
   road-leg distances including station detours. Reject infeasible road legs.

Station selection is a heuristic, NOT a globally cheapest route. The greedy
purchase quantities are optimal for the FINAL FIXED station sequence under the
stated constant-MPG, divisible-fuel model. Rerouting may change the best station
selection; the prototype does not iterate to a global solution. A detour can
make the selection infeasible; 422 is returned rather than inventing a stop.
For stronger optimization, construct a directed road-distance candidate graph
and solve a fuel-state shortest-path or linear/mixed-integer optimization model,
including detour fuel costs and comparing alternative routes.

50 gallons = 500 miles / 10 MPG. Default reserve is 2 gallons, so usable range
is 480 miles. Set reserve_gallons=0 for the literal 500-mile assessment model,
but that leaves no safety margin. Starts full by default. Initial fuel cost is
EXCLUDED because its acquisition price is unknown. Total is money purchased
during this trip, not the replacement value of all fuel consumed. A short trip
can therefore cost $0 in additional purchases. To price all consumed fuel,
provide an initial acquisition price and choose an inventory valuation policy.
No automatic origin purchase is assumed; low initial fuel can yield 422.

CSV prices are treated as USD per US gallon, with no fuel-grade/date metadata.
Duplicate OPIS IDs use the median, an explicit assessment assumption, not a
claim that the cheapest duplicate price is currently available. Canadian rows
are excluded using a USA state/DC allowlist. Resolve duplicates by fuel type
and timestamp if those fields become available. Price imports preserve verified
coordinates; reverify them if station identities/addresses change.

Coordinates and snap-to-road access still need real-world review. driving-car
is not truck-specific routing. No vehicle dimensions, taxes, toll costs, traffic,
closures, price freshness, or fuel-type compatibility are modeled.
Hosted ORS allows at most 50 waypoints and driving routes up to 6,000 km;
profile restrictions can impose additional limits. No-route cases are supported,
including disconnected regions. A USA-only driving route to Alaska from the
contiguous USA may not exist without crossing Canada.

## Deployment

Add authentication, per-user quotas, shared cache/rate limits, structured logs,
background geocoding, database spatial indexing, provider retry/backoff, and
provider response-schema checks. SQLite and file cache are prototype defaults.
Anonymous DRF throttling is not a security boundary or a global provider quota.
Use a production WSGI/ASGI server, a real secret, DEBUG=0, HTTPS, and appropriate
ALLOWED_HOSTS. Never expose ORS_API_KEY to the browser. Error responses currently
use 502 for provider failures and 422 for infeasible plans.

Leaflet: https://leafletjs.com/examples/geojson/
ORS options: https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/routing-options
OSM tile policy: https://operations.osmfoundation.org/policies/tiles/
The demo uses standard OSM tiles with attribution. Do not bulk-download/prefetch;
for production traffic select a suitable tile provider and follow its policy.
No public Nominatim bulk geocoding is used.
