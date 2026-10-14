import math
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .service import plan
from .provider import ProviderError
from .optimizer import Infeasible
class Input(serializers.Serializer):
    start = serializers.CharField(max_length=250)
    finish = serializers.CharField(max_length=250)
    initial_fuel_gallons = serializers.FloatField(default=50,min_value=0,max_value=50)
    reserve_gallons = serializers.FloatField(default=2,min_value=0,max_value=10)
    corridor_miles = serializers.FloatField(default=2,min_value=0.1,max_value=10)
    def validate(self,data):
        if not all(math.isfinite(data[k]) for k in ("initial_fuel_gallons", "reserve_gallons", "corridor_miles")):
            raise serializers.ValidationError("Numeric inputs must be finite.")
        if data["initial_fuel_gallons"] < data["reserve_gallons"]:
            raise serializers.ValidationError("Initial fuel must cover the reserve.")
        return data
class PlanView(APIView):
    def post(self,request):
        serializer = Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(plan(serializer.validated_data))
        except Infeasible as exc:
            return Response({"error":str(exc)},status=422)
        except ProviderError as exc:
            return Response({"error":str(exc)},status=status.HTTP_502_BAD_GATEWAY)
