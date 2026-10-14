from dataclasses import dataclass
@dataclass
class Stop:
    mile: float
    price: float
    station: object = None

class Infeasible(Exception):
    pass

def optimize(stops, destination_miles, initial_gallons=50, reserve_gallons=2):
    """Minimum purchase cost on a FIXED ordered route with divisible fuel.
    Initial fuel is already owned; preserve the reserve at every arrival.
    """
    capacity = 50 - reserve_gallons
    fuel = initial_gallons - reserve_gallons
    if fuel < 0:
        raise Infeasible("Initial fuel is below the requested reserve.")
    nodes = [Stop(0, float("inf"))] + sorted(stops, key=lambda s: s.mile) + [Stop(destination_miles, 0)]
    purchases = []
    for i, current in enumerate(nodes[:-1]):
        next_gap = (nodes[i+1].mile - current.mile) / 10
        if next_gap > capacity + 1e-7:
            raise Infeasible("No reachable station in the available dataset on this route.")
        if i == 0:
            buy = 0
        else:
            cheaper = next((n for n in nodes[i+1:]
                if n.mile - current.mile <= capacity * 10 + 1e-7 and n.price < current.price), None)
            target = (cheaper.mile - current.mile) / 10 if cheaper else min(capacity, (destination_miles-current.mile)/10)
            buy = max(0, target-fuel)
        arrival = fuel + reserve_gallons
        fuel += buy
        if buy > 1e-7:
            purchases.append({"station": current.station, "mile": current.mile,
                "gallons": buy, "price": current.price, "cost": buy*current.price,
                "arrival_gallons": arrival, "departure_gallons": fuel+reserve_gallons})
        fuel -= next_gap
        if fuel < -1e-7:
            raise Infeasible("Initial fuel cannot reach the first available station, or road detours exceed available fuel.")
        fuel = max(0, fuel)
    return purchases, fuel + reserve_gallons
