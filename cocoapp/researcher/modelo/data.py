
from researcher.models import DataClimImputation
from agricultural_engineer.models import DataApiNasaImputation
from django.db.models import Max
from datetime import timedelta
from django_pandas.io import read_frame

def import_data_clim(pkFinca, days=179, perfil='investigador'):
    if perfil == 'investigador':
        max_date = DataClimImputation.objects.filter(api_parameters_finca=pkFinca).aggregate(Max('date'))['date__max']
        date_180_days_before_max = max_date - timedelta(days=days)
        objImputation = DataClimImputation.objects.filter(
                                                            api_parameters_finca=pkFinca,
                                                            date__gte=date_180_days_before_max,
                                                            date__lte=max_date
                                                        )
    else:
        max_date = DataApiNasaImputation.objects.filter(api_parameters_finca=pkFinca).aggregate(Max('date'))['date__max']
        date_180_days_before_max = max_date - timedelta(days=days)
        objImputation = DataClimImputation.objects.filter(
                                                            api_parameters_finca=pkFinca,
                                                            date__gte=date_180_days_before_max,
                                                            date__lte=max_date
                                                        )
        
    df = read_frame(objImputation)

    df = df.drop(columns=['api_parameters_finca'])
    df = df.drop(columns=['id'])
    df = df.drop(columns=['created'])
    df = df.drop(columns=['updated'])
    return df