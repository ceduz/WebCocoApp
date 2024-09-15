from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('aPIParameterNasaFinca/', login_required(APIParameterNasaFincaListView.as_view()), name="aPIParameterNasaFinca"),
    path('aPIParameterNasaFinca/dt/', login_required(get_api_parameter_dt), name='aPIParameterNasaFinca-dt'),
    path('aPIParameterNasaFinca/create/', login_required(APIParameterNasaFincaCreateView.as_view()), name='api_parameter_nasa_finca-create'),
    path('aPIParameterNasaFinca/finca/<int:id_filtrado>/', login_required(DataClimFincaListView.as_view()), name='api_parameter_nasa_finca-select'),
    path('aPIParameterNasaFinca/climImput/dt/', login_required(get_api_imputation_dt), name='dataApiNasaImputation-dt'),
    path('aPIParameterNasaFinca/pronosticDay/dt/', login_required(get_pronostic_day_dt), name='dataPronosticDayModel-dt'),
    path('aPIParameterNasaFinca/pronostic/create/', login_required(set_pronostic_model), name='pronostic-create'),
    path('aPIParameterNasaFinca/updateChart/', login_required(get_data_rangeImputAgri), name='updateChart-agr'),
    path('aPIParameterNasaFinca/drenIrrig/create/', login_required(set_two_stage_model), name='drenIrrig-create'),
    #TwoStageFincaModel
    path('aPIParameterNasaFinca/twoStageFincaModel/delete/<int:pk>/', login_required(TwoStageFincaModelDeleteView.as_view()), name='twoStageFincaModel-delete'),
    #BeastPronosticModel
    path('aPIParameterNasaFinca/beastPronosticModel/delete/<int:pk>/', login_required(delete_beast_pronostic), name='beastPronosticModel-delete'),
    path('aPIParameterNasaFinca/beastPronosticModel/chart/', login_required(get_data_farmer_chart), name='beastPronosticModel-chart'),
    #APIParameterNasaFinca
    path('aPIParameterNasaFinca/APIParameterNasaFinca/delete/<int:pk>/', login_required(APIParameterNasaFincaDeleteView.as_view()), name='APIParameterNasaFinca-delete'),
]