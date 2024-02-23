from django.shortcuts import render, HttpResponse
from django.views.generic.base import TemplateView

# Create your views here.
class HomePageView(TemplateView):
    template_name = "farmer/weather_forecast.html"


"""
def weather_forecast(request):
    return render(request, "farmer/weather_forecast.html")
"""