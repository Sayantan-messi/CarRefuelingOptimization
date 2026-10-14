from django.db import models
class Station(models.Model):
    opis_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=250)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=150)
    state = models.CharField(max_length=2)
    price = models.DecimalField(max_digits=12, decimal_places=8)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    verified = models.BooleanField(default=False)
