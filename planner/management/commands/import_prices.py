import csv
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from planner.models import Station
US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
class Command(BaseCommand):
    help = "Import USA prices. Duplicate IDs use median price, not an unjustified minimum."
    def add_arguments(self,parser):
        parser.add_argument("csv_path")
    def handle(self,*args,**options):
        groups = {}
        with open(options["csv_path"],encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f):
                row = {k:v.strip() for k,v in row.items()}
                if row["State"] not in US_STATES:
                    continue
                try:
                    price = Decimal(row["Retail Price"])
                    sid = int(row["OPIS Truckstop ID"])
                    if not price.is_finite() or price <= 0:
                        continue
                except (InvalidOperation,ValueError):
                    continue
                groups.setdefault(sid,[]).append((price,row))
        for sid,rows in groups.items():
            prices = sorted(p for p,r in rows)
            n = len(prices)
            median = prices[n//2] if n%2 else (prices[n//2-1]+prices[n//2])/2
            r = rows[0][1]
            Station.objects.update_or_create(opis_id=sid,defaults={"name":r["Truckstop Name"],
                "address":r["Address"],"city":r["City"],"state":r["State"],"price":median})
        self.stdout.write(f"Imported {len(groups)} USA stations; duplicate price policy: median.")
