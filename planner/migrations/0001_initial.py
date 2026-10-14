from django.db import migrations, models
class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [migrations.CreateModel(name="Station", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("opis_id", models.PositiveIntegerField(unique=True)),
        ("name", models.CharField(max_length=250)),
        ("address", models.CharField(max_length=500)),
        ("city", models.CharField(max_length=150)),
        ("state", models.CharField(max_length=2)),
        ("price", models.DecimalField(max_digits=12, decimal_places=8)),
        ("longitude", models.FloatField(null=True)),
        ("latitude", models.FloatField(null=True)),
        ("verified", models.BooleanField(default=False)),
    ])]
