# Fuel Route Planner

This application calculates the most cost-effective fuel stops between two locations in the United States. The user enters a start and destination location, the system calculates the driving route, identifies fuel stations near the route using the supplied fuel-price dataset, determines optimal refueling locations based on fuel prices and vehicle range constraints (500 miles / 10 MPG), and returns the route, recommended fuel stops, and estimated fuel cost.

---

# System Flow

```text
┌─────────────────┐
│     User        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Django API      │
│ POST /api/route │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Geocode Start   │
│ & Destination   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Route Service   │
│ (OSRM)          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Locate Nearby   │
│ Fuel Stations   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Fuel Cost       │
│ Optimization    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Route + Stops + │
│ Fuel Cost       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Browser Map UI  │
└─────────────────┘
```

---

# Running with Docker

## Prerequisites

- Docker Desktop installed and running.

## Build and Start

From the project root:

```bash
docker compose up --build
```

Or detached mode:

```bash
docker compose up -d --build
```

## Open the Application

```text
http://localhost:8000
```

## Stop the Application

```bash
docker compose down
```

---

# Running Manually

## Prerequisites

- Python 3.11+
- pip

## Create Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment

Copy:

```bash
.env.example
```

to:

```bash
.env
```

and update any required configuration values.

## Run Database Migrations

```bash
python manage.py migrate
```

## Import Fuel Data

```bash
python manage.py import_prices data/fuel-prices-for-be-assessment.csv
```

## Start the Server

```bash
python manage.py runserver
```

## Open the Application

```text
http://127.0.0.1:8000
```

---

# API Example

Endpoint:

```http
POST /api/route/
```

Example Request:

```json
{
  "start": "Dallas, TX",
  "finish": "Los Angeles, CA"
}
```

Example Response:

```json
{
  "distance_miles": 1435.2,
  "total_fuel_cost_usd": 387.45,
  "fuel_stops": [...],
  "route_geojson": {...}
}
```

---

# Assumptions

- Vehicle range: 500 miles
- Fuel economy: 10 MPG
- Fuel prices are loaded from the supplied CSV dataset
- Fuel stop recommendations are selected based on route proximity and fuel price optimization