from django.shortcuts import render, HttpResponse
from django.views.generic.base import TemplateView
from django.http import JsonResponse, Http404
import requests
import datetime
import locale


# Create your views here.
class HomePageView(TemplateView):
    template_name = "farmer/weather_forecast.html"

"""
def weather_forecast(request):
    return render(request, "farmer/weather_forecast.html")
"""

def weather_farecast(request):
    if request.user.is_authenticated:
        latitud = request.GET.get('lat', None)
        longitud = request.GET.get('lon', None)

        API_KEY_WEATHER = open("API_KEY_WEATHER", "r").read()
        current_url = "https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid={}"
        
        daily_weather = fetch_weather(API_KEY_WEATHER, current_url, latitud, longitud)

        return JsonResponse(daily_weather, safe=False)
    else:
        raise Http404("Usuario no autenticado.")

def fetch_weather(api_key, current_url, latitud, longitud):
    #response = requests.get(current_url.format('7.1253900','-73.1198000', api_key)).json()
    response = requests.get(current_url.format(latitud,longitud, api_key)).json()

    daily_weather = []
    if response['cod'] == "200":
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

        daily_weather.append({
            'cod': response['cod'],
            'lat': response['city']['coord']['lat'],
            'lon': response['city']['coord']['lon'],
        })
        for daily_data in response['list'][:5]:
            daily_weather.append({
                'day' : datetime.datetime.utcfromtimestamp(daily_data['dt']).strftime('%A').capitalize(),
                'date': datetime.datetime.utcfromtimestamp(daily_data['dt']).strftime('%d de %B de %Y Hr: %H:%M'),
                'min_temp': round(daily_data['main']['temp_min'] - 273.15, 0),
                'max_temp': round(daily_data['main']['temp_max'] - 273.15, 0),
                'description': daily_data['weather'][0]['description'],
                'icon': daily_data['weather'][0]['icon'],
            })
    else:
        try:
            daily_weather.append({
                'cod' : response['cod'],
                'message' : 'Ocurrio un error al traer los datos del API.',
                'message_api' : response['message'],
            })
        except:
            raise Http404("Error al traer los datos del API.")

    return daily_weather