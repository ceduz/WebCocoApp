from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(HomePageView.as_view()), name="index_farmer"),
    path('farmer/weather', weather_farecast, name="weather"),
    #myFinca
    path('myFinca/', login_required(MiFincaListView.as_view()), name="myFinca"),
    path('myFinca/<int:pk>/update/', login_required(MiFincaUpdateView.as_view()), name='myFinca-update'),
    path('myFinca/create/', login_required(MiFincaCreateView.as_view()), name='myFinca-create'),
    #CultivationNovelty
    path('cultivationNovelty/', login_required(CultivationNoveltyListView.as_view()), name="cultivationNovelty"),
    path('cultNov/<int:pk>/update/', login_required(CultNovUpdateView.as_view()), name='cultNov-update'),
    path('cultNov/create/', login_required(CultNovCreateView.as_view()), name='cultNov-create'),
    #Inventory
    path('inventory/', login_required(InventoryListView.as_view()), name="inventory"),
    path('inventory/<int:pk>/update/', login_required(InventoryUpdateView.as_view()), name='inventory-update'),
    path('inventory/create/', login_required(InventoryCreateView.as_view()), name='inventory-create'),
]