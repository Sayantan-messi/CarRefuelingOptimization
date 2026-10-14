from django.urls import path
from django.shortcuts import render
from planner.views import PlanView
urlpatterns = [path("api/route/", PlanView.as_view()), path("", lambda request: render(request, "map.html"))]
