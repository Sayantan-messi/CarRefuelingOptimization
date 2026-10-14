#!/bin/sh

echo "Running migrations..."

python manage.py migrate

echo "Importing fuel prices..."

python manage.py import_prices \
    data/fuel-prices-for-be-assessment.csv || true

echo "Starting Django..."

python manage.py runserver 0.0.0.0:8000
