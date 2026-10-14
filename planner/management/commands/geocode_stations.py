import csv, time
from django.core.management.base import BaseCommand
from planner.models import Station
from planner.provider import search, ProviderError
class Command(BaseCommand):
    help = "Export geocoding suggestions for manual review; never mark city centroids as stations."
    def add_arguments(self,parser):
        parser.add_argument("output")
        parser.add_argument("--limit",type=int,default=100)
        parser.add_argument("--state",default="")
    def handle(self,*args,**options):
        qs = Station.objects.filter(verified=False).order_by("opis_id")
        if options["state"]:
            qs = qs.filter(state=options["state"].upper())
        with open(options["output"],"w",newline="",encoding="utf-8") as f:
            writer = csv.DictWriter(f,fieldnames=["opis_id","name","city","state","longitude","latitude","matched_label","confidence","verified"])
            writer.writeheader()
            for s in qs[:options["limit"]]:
                try:
                    feature = search(f"{s.name}, {s.address}, {s.city}, {s.state}, USA",station=True)
                    lon,lat = feature["geometry"]["coordinates"][:2]
                    props = feature["properties"]
                    writer.writerow(dict(opis_id=s.opis_id,name=s.name,city=s.city,state=s.state,
                        longitude=lon,latitude=lat,matched_label=props.get("label",""),
                        confidence=props.get("confidence",""),verified="false"))
                except ProviderError as exc:
                    self.stderr.write(f"{s.opis_id}: {exc}")
                    if "quota" in str(exc).lower():
                        break
                time.sleep(1.1)
        self.stdout.write("Review suggestions, correct coordinates, set verified=true, then import_coordinates.")
