import csv, math
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from planner.models import Station
class Command(BaseCommand):
    help = "Import manually verified USA station coordinates keyed by OPIS ID."
    def add_arguments(self,parser):
        parser.add_argument("csv_path")
    @transaction.atomic
    def handle(self,*args,**options):
        count = 0
        with open(options["csv_path"],encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f):
                if r.get("verified","").strip().lower() != "true":
                    continue
                lon,lat = float(r["longitude"]),float(r["latitude"])
                if not (math.isfinite(lon) and math.isfinite(lat) and -180<=lon<=180 and -90<=lat<=90):
                    raise CommandError("Invalid coordinates.")
                count += Station.objects.filter(opis_id=int(r["opis_id"])).update(longitude=lon,latitude=lat,verified=True)
        self.stdout.write(f"Imported {count} verified coordinates. Verification must include station identity and USA location.")
