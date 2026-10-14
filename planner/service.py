from pyproj import Transformer, Geod
from shapely.geometry import LineString, Point
from .models import Station
from .provider import search, route, ProviderError
from .optimizer import Stop, optimize, Infeasible
METER_PER_MILE = 1609.344

def candidates(feature, corridor_miles):
    # Local azimuthal projection, not distances measured in latitude degrees.
    coordinates = feature["geometry"]["coordinates"]
    lon, lat = coordinates[len(coordinates)//2][:2]
    transform = Transformer.from_crs("EPSG:4326", f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m", always_xy=True)
    line = LineString([transform.transform(*p[:2]) for p in coordinates])
    geod = Geod(ellps="WGS84")
    projected = list(line.coords)
    cumulative = [0.0]
    for a,b in zip(coordinates, coordinates[1:]):
        cumulative.append(cumulative[-1] + geod.inv(a[0], a[1], b[0], b[1])[2])
    total = feature["properties"]["summary"]["distance"] / METER_PER_MILE
    result = []
    for station in Station.objects.filter(verified=True, latitude__isnull=False, longitude__isnull=False).iterator():
        point = Point(*transform.transform(station.longitude, station.latitude))
        if point.distance(line) > corridor_miles*METER_PER_MILE:
            continue
        # Identify closest segment and interpolate geodesic cumulative distance.
        best = None
        for k,(a,b) in enumerate(zip(projected, projected[1:])):
            dx,dy = b[0]-a[0],b[1]-a[1]
            norm = dx*dx+dy*dy
            t = max(0,min(1,((point.x-a[0])*dx+(point.y-a[1])*dy)/norm)) if norm else 0
            d = (point.x-a[0]-t*dx)**2+(point.y-a[1]-t*dy)**2
            if best is None or d < best[0]:
                best = (d, cumulative[k]+t*(cumulative[k+1]-cumulative[k]))
        mile = best[1]/cumulative[-1]*total if cumulative[-1] else 0
        if 0.001 < mile < total-0.001:
            result.append(Stop(mile, float(station.price), station))
    return sorted(result, key=lambda s:s.mile), total

def plan(data):
    start = search(data["start"])["geometry"]["coordinates"][:2]
    finish = search(data["finish"])["geometry"]["coordinates"][:2]
    base = route([start,finish])
    available, distance = candidates(base, data["corridor_miles"])
    selected, _ = optimize(available, distance, data["initial_fuel_gallons"], data["reserve_gallons"])
    stations = [p["station"] for p in selected]
    final = route([start]+[[s.longitude,s.latitude] for s in stations]+[finish]) if stations else base
    segments = final["properties"].get("segments", [])
    if len(segments) != len(stations)+1:
        raise ProviderError("Provider returned unexpected route segments.")
    positions, miles = [], 0.0
    for index,segment in enumerate(segments):
        miles += segment["distance"]/METER_PER_MILE
        if index < len(stations):
            positions.append(Stop(miles,float(stations[index].price),stations[index]))
    # Recalculate purchase quantities using actual road legs, including detours.
    purchases, remaining = optimize(positions,miles,data["initial_fuel_gallons"],data["reserve_gallons"])
    stops = []
    for p in purchases:
        s = p["station"]
        stops.append({"opis_id": s.opis_id, "name": s.name, "address": s.address,
            "city": s.city, "state": s.state, "latitude": s.latitude, "longitude": s.longitude,
            "route_mile": round(p["mile"],3), "price_per_gallon": str(s.price),
            "gallons_to_buy": round(p["gallons"],6), "cost_usd": round(p["cost"],2),
            "arrival_fuel_gallons": round(p["arrival_gallons"],6),
            "departure_fuel_gallons": round(p["departure_gallons"],6)})
    return {"route_geojson": final, "start_coordinates": start, "finish_coordinates": finish,
        "distance_miles": round(miles,3), "fuel_consumed_gallons": round(miles/10,6),
        "fuel_purchased_gallons": round(sum(p["gallons"] for p in purchases),6),
        "total_fuel_cost_usd": round(sum(p["cost"] for p in purchases),2),
        "remaining_fuel_gallons": round(remaining,6), "fuel_stops": stops,
        "visited_station_ids": [s.opis_id for s in stations],
        "assumptions": {"mpg":10,"tank_gallons":50, "initial_fuel_gallons":data["initial_fuel_gallons"],
            "reserve_gallons":data["reserve_gallons"], "initial_fuel_cost_included":False,
            "price_source":"CSV snapshot; USD per US gallon assumed",
            "optimization":"Heuristic station selection in baseline corridor; optimal quantities for final fixed station sequence, not globally optimal route."},
        "warnings": ["Station coordinates must be verified. Prices are not live.",
            "Road detours are checked, but infeasible selections return 422 rather than an unsafe plan.",
            "All visited waypoints remain on the map, even if recalculation requires no purchase there."],
        "attribution":"openrouteservice; OpenStreetMap contributors"}
