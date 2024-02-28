from django.urls import path
from .views import HomePageView, weather_farecast

urlpatterns = [
    path('', HomePageView.as_view(), name="index_farmer"),
    path('farmer/weather', weather_farecast, name="weather"),
]