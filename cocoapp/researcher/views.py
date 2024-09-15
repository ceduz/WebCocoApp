from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import *
from farmer.models import Finca
from django.db.models import Max, Min, Q, ProtectedError
from .forms import *
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
import pandas as pd
import pickle

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import norm
import io
import base64
import json
import ast

from django.utils.decorators import method_decorator
from .modelo.import_data_api import get_data
from .modelo.imputation_date import imputation
from .modelo.data import import_data_clim
from .modelo.decision_model import main_model_deterministic
from .modelo.modelling import iterative_modeling
from .modelo.forecast_scenarios import forecast_scenarios
from .modelo.merge_scenarios import merge_scenarios
from .modelo.two_stage_opti_model import main
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse

import requests
matplotlib.use('Agg')  # Use el backend 'Agg' para evitar problemas con GUI

def researcher_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                if request.user.userprofile.profile.profile == "Investigador":
                    pass
            except:
                raise Http404("No existe perfil asociado al usuario. Comuníquese con el administrador del sistema.")

            
            if request.user.userprofile.profile.profile == "Investigador":
                return view_func(request, *args, **kwargs)
            else:
                raise Http404("Usuario no tiene permisos suficientes.")               
            
        else:
            raise Http404("Usuario no autenticado.")
    return _wrapped_view

#-----------------------------------------------------------------------------------------------------------------------------
#Start script ApiParametersFincaListView

class ApiParametersFincaListView(LoginRequiredMixin, ListView):
    model = ApiParametersFinca
    template_name = 'researcher/climatological_list.html'
    context_object_name = 'apiParametersFinca'

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    
class ApiParametersFincaCreateView(LoginRequiredMixin, CreateView):
    form_class = ApiParametersFincaForm
    template_name = 'researcher/climatological_add.html'

    def get_success_url(self):
        return reverse_lazy('climatological-create')

    def form_valid(self, form):     
        instance = form.save(commit=False)
        pkFinca = instance.finca.pk

        try:
            if pkFinca:
                finca = Finca.objects.get(pk=pkFinca)
                form.instance.latitud = finca.latitud
                form.instance.longitud = finca.longitud             
        except Finca.DoesNotExist:
            form.add_error('finca', 'No la finca seleccionada.')
            return self.form_invalid(form)
        except AttributeError:
            form.add_error('finca', 'No existe latitud registrada en la finca.')
            form.add_error('finca', 'No existe longitud registrada en la finca.')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, "Ocurrio un error en el aplicativo: {}".format(e))
            #return HttpResponseRedirect(self.get_success_url())
            return self.form_invalid(form)
               
        date_current = datetime.now()
        date_current2 = datetime.now()
        year = (date_current - timedelta(days=365 * 5)).year
        date_4_years_ago = datetime(year, 1, 1)

        form.instance.date_start = timezone.make_aware(date_4_years_ago, timezone.get_current_timezone())
        form.instance.date_end = timezone.make_aware(date_current2, timezone.get_current_timezone())
        latitud = form.instance.latitud 
        longitud = form.instance.longitud 
        
        try:
            df = get_data(date_4_years_ago, date_current2, latitud, longitud)
        except Exception as e:
            messages.error(self.request, "Ocurrio un error en el aplicativo: {}".format(e))
            #return HttpResponseRedirect(self.get_success_url())
            return self.form_invalid(form)
        
        instance.save()
        data_api_nasa_objects = []

        # Iterar sobre el DataFrame y crear objetos DataApiNasa
        try:
            for index, row in df.iterrows():
                data_api_nasa_objects.append(
                    DataApiNasa(
                        api_parameters_finca=instance,
                        date=row['date'],
                        allsky_sfc_sw_dwn=row['ALLSKY_SFC_SW_DWN'],
                        clrsky_sfc_sw_dwn=row['CLRSKY_SFC_SW_DWN'],
                        t2m_max=row['T2M_MAX'],
                        t2m_min=row['T2M_MIN'],
                        t2mdew=row['T2MDEW'],
                        prectotcorr=row['PRECTOTCORR'],
                        rh2m=row['RH2M'],
                        ws2m=row['WS2M']
                    )
                )
            DataApiNasa.objects.bulk_create(data_api_nasa_objects) # Usar bulk_create para guardar todos los objetos a la vez
        except Exception as e:
            messages.error(self.request, "Ocurrio un error en el aplicativo: {}".format(e))
            return self.form_invalid(form)

        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ApiParametersFincaDeleteView(DeleteView):
    model = ApiParametersFinca
    success_url = 'researcher/dataNasa_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.finca
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                obj = ApiParametersFinca.objects.get(finca=id)
            except ApiParametersFinca.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Datos de la nasa seleccionado no encontrado.', 'type':'delete'})
            
            try:
                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 
                    return JsonResponse({'status': 'success', 'message': 'Los datos seleccionados ({}), fueron eliminados correctamente.'.format(id), 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar los datos seleccionados.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar los datos seleccionados porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})
    

def update_data_nasa(request):
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    response_data = {}
    if request.user.userprofile.profile.profile == "Investigador":
        if request.method == 'POST' and is_ajax:
            pk = request.POST.get('pk')
            if pk:
                try:
                    instance_finca = Finca.objects.get(owner_name_id=pk)
                    instance_ApiParam = ApiParametersFinca.objects.get(finca_id=pk)

                    instance_ApiParam.latitud = instance_finca.latitud
                    instance_ApiParam.longitud = instance_finca.longitud

                    date_current = datetime.now()
                    date_current2 = datetime.now()
                    year = (date_current - timedelta(days=365 * 5)).year
                    date_4_years_ago = datetime(year, 1, 1)

                    instance_ApiParam.date_start  = timezone.make_aware(date_4_years_ago, timezone.get_current_timezone())
                    instance_ApiParam.date_end  = timezone.make_aware(date_current2, timezone.get_current_timezone())

                    df = get_data(date_4_years_ago, date_current2, instance_ApiParam.latitud, instance_ApiParam.longitud)

                    instance_ApiParam.save()
                    DataApiNasa.objects.filter(api_parameters_finca_id=pk).delete()
                    data_api_nasa_objects = []

                    for index, row in df.iterrows():
                        data_api_nasa_objects.append(
                            DataApiNasa(
                                api_parameters_finca=instance_ApiParam,
                                date=row['date'],
                                allsky_sfc_sw_dwn=row['ALLSKY_SFC_SW_DWN'],
                                clrsky_sfc_sw_dwn=row['CLRSKY_SFC_SW_DWN'],
                                t2m_max=row['T2M_MAX'],
                                t2m_min=row['T2M_MIN'],
                                t2mdew=row['T2MDEW'],
                                prectotcorr=row['PRECTOTCORR'],
                                rh2m=row['RH2M'],
                                ws2m=row['WS2M']
                            )
                        )
                    DataApiNasa.objects.bulk_create(data_api_nasa_objects)

                    obj_type_imput = TypeImpFieldDataClima.objects.filter(finca=pk).first()

                    if obj_type_imput:
                        try:
                            df_result = imputation(pk, 
                                                    instance_finca.name, 
                                                    obj_type_imput.allsky_sfc_sw_dwn,
                                                    obj_type_imput.clrsky_sfc_sw_dwn,
                                                    obj_type_imput.t2m_max,
                                                    obj_type_imput.t2m_min,
                                                    obj_type_imput.t2mdew,
                                                    obj_type_imput.prectotcorr,
                                                    obj_type_imput.rh2m,
                                                    obj_type_imput.ws2m)  
                            
                            data_df_objects = []
                        
                            DataClimImputation.objects.filter(api_parameters_finca=pk).delete()
                            for index, row in df_result.iterrows():
                                data_df_objects.append(
                                    DataClimImputation(
                                        api_parameters_finca=obj_type_imput,
                                        date=row['date'],
                                        allsky_sfc_sw_dwn=row['allsky_sfc_sw_dwn'],
                                        clrsky_sfc_sw_dwn=row['clrsky_sfc_sw_dwn'],
                                        t2m_max=row['t2m_max'],
                                        t2m_min=row['t2m_min'],
                                        t2mdew=row['t2mdew'],
                                        prectotcorr=row['prectotcorr'],
                                        rh2m=row['rh2m'],
                                        ws2m=row['ws2m']
                                    )
                                )
                            DataClimImputation.objects.bulk_create(data_df_objects) 
                        except Exception as e:
                            print(str(e))
                            TypeImpFieldDataClima.objects.filter(finca=pk).delete()
                            DataClimImputation.objects.filter(api_parameters_finca=pk).delete()
                            

                except Finca.DoesNotExist:
                    response_data = {'status': 'error', 'message' : 'No se encontró ninguna finca con el ID proporcionado.'}
                    return JsonResponse(response_data)
                except ApiParametersFinca.DoesNotExist:
                    response_data = {'status': 'error', 'message' : 'No se encontró ninguna finca con el ID proporcionado.'}
                    return JsonResponse(response_data)
                except Exception as e:
                    response_data = {'status': 'error', 'message' : '{}'.format(e)}
                    return JsonResponse(response_data)
                

                response_data = {'status': 'aprobado', 'message': f'Los datos climatologicos para la finca {instance_finca.name} han sido actualizados correctamente.'}
                return JsonResponse(response_data)
            else:
                return JsonResponse({'error': 'La finca no fue proporcionada.'}, status=400)
        else:
            # Si la solicitud no es Ajax o no es POST, devolver un error
            return JsonResponse({'error': 'La solicitud no es valida.'}, status=400)
    else:
        return JsonResponse({'error': 'No tiene el rol necesario para ejecutar este proceso.'}, status=400)


class DataNasaListView(LoginRequiredMixin, ListView):
    model = DataApiNasa
    template_name = 'researcher/dataNasa_list.html'
    context_object_name = 'dataApiNasa'

    def get_queryset(self):
        id_filtrado = self.kwargs['id_filtrado']  # Obtener el ID filtrado desde la UR
        queryset = DataApiNasa.objects.filter(api_parameters_finca=id_filtrado)
        return queryset

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
#End script ApiParametersFincaListView
#-----------------------------------------------------------------------------------------------------------------------------
#Start script TypeImpFieldDataClimaListView

class TypeImpFieldDataClimaListView(LoginRequiredMixin, ListView):
    model = TypeImpFieldDataClima
    template_name = 'researcher/imputationColumn_list.html'
    context_object_name = 'typeImpFieldDataClima'

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
      

class TypeImpFieldDataClimaCreateView(LoginRequiredMixin, CreateView):
    form_class = TypeImpFieldDataClimaForm
    template_name = 'researcher/imputacionColumn_add.html'

    def get_success_url(self):
        return reverse_lazy('typeImpFieldDataClima-create')


    def form_valid(self, form):     
        instance = form.save(commit=False)
        pkFinca = instance.finca.pk
        name_finca = None
        try:
            if pkFinca:
                finca = Finca.objects.get(pk=pkFinca)      
                name_finca = finca.name    
        except Finca.DoesNotExist:
            form.add_error('finca', 'No la finca seleccionada.')
            return self.form_invalid(form)


        try:
            df_result = imputation('researcher',
                                    pkFinca, 
                                    name_finca, 
                                    instance.allsky_sfc_sw_dwn,
                                    instance.clrsky_sfc_sw_dwn,
                                    instance.t2m_max,
                                    instance.t2m_min,
                                    instance.t2mdew,
                                    instance.prectotcorr,
                                    instance.rh2m,
                                    instance.ws2m)  
        except Exception as e:
            form.add_error('finca', '{}'.format(e))
            return self.form_invalid(form)
               
        data_df_objects = []
        instance.save()

        try:
            for index, row in df_result.iterrows():
                data_df_objects.append(
                    DataClimImputation(
                        api_parameters_finca=instance,
                        date=row['date'],
                        allsky_sfc_sw_dwn=row['allsky_sfc_sw_dwn'],
                        clrsky_sfc_sw_dwn=row['clrsky_sfc_sw_dwn'],
                        t2m_max=row['t2m_max'],
                        t2m_min=row['t2m_min'],
                        t2mdew=row['t2mdew'],
                        prectotcorr=row['prectotcorr'],
                        rh2m=row['rh2m'],
                        ws2m=row['ws2m']
                    )
                )
            DataClimImputation.objects.bulk_create(data_df_objects) 
        except Exception as e:
            messages.error(self.request, 'Ocurrio al guardar los datos imputados: {}'.format(e))
            return self.form_invalid(form)
        
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)
    
    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class TypeImpFieldDataClimaDeleteView(DeleteView):
    model = TypeImpFieldDataClima
    success_url = 'researcher/imputationColumn_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.finca
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                obj = TypeImpFieldDataClima.objects.get(finca=id)
            except TypeImpFieldDataClima.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Datos del proceso de imputación no encontrado.', 'type':'delete'})
            
            try:
                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 
                    return JsonResponse({'status': 'success', 'message': 'Los datos del proceso de imputación ({}), fueron eliminados correctamente.'.format(id), 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar los datos seleccionados.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar los datos seleccionados porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})


class TypeImpFieldDataClimaUpdateView(LoginRequiredMixin, UpdateView):
    model = TypeImpFieldDataClima
    form_class = TypeImpFieldDataClimaFormUpd
    template_name = 'researcher/imputacionColumn_form.html'
    context_object_name = 'typeImpFieldDataClima'

    def get_success_url(self):
        return reverse_lazy('typeImpFieldDataClima-update', args=[self.object.finca_id])

    def get_object(self, queryset=None):
        return get_object_or_404(TypeImpFieldDataClima, finca_id=self.kwargs['pk'])

    def form_valid(self, form):
        instance = form.save(commit=False)
        pkFinca = instance.finca.pk
        name_finca = None
        try:
            if pkFinca:
                finca = Finca.objects.get(pk=pkFinca)      
                name_finca = finca.name    
        except Finca.DoesNotExist:
            form.add_error('finca', 'No la finca seleccionada.')
            return self.form_invalid(form)


        try:
            df_result = imputation(pkFinca, 
                                    name_finca, 
                                    instance.allsky_sfc_sw_dwn,
                                    instance.clrsky_sfc_sw_dwn,
                                    instance.t2m_max,
                                    instance.t2m_min,
                                    instance.t2mdew,
                                    instance.prectotcorr,
                                    instance.rh2m,
                                    instance.ws2m)  
        except Exception as e:
            form.add_error('finca', '{}'.format(e))
            return self.form_invalid(form)
               
        data_df_objects = []
        instance.save()
        
        DataClimImputation.objects.filter(api_parameters_finca=pkFinca).delete()
        for index, row in df_result.iterrows():
            data_df_objects.append(
                DataClimImputation(
                    api_parameters_finca=instance,
                    date=row['date'],
                    allsky_sfc_sw_dwn=row['allsky_sfc_sw_dwn'],
                    clrsky_sfc_sw_dwn=row['clrsky_sfc_sw_dwn'],
                    t2m_max=row['t2m_max'],
                    t2m_min=row['t2m_min'],
                    t2mdew=row['t2mdew'],
                    prectotcorr=row['prectotcorr'],
                    rh2m=row['rh2m'],
                    ws2m=row['ws2m']
                )
            )
        DataClimImputation.objects.bulk_create(data_df_objects) 
                
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

def get_data_imput_chart(request):

    if request.user.userprofile.profile.profile == "Investigador":
        obj = TypeImpFieldDataClima.objects.all()
        return render(request, "researcher/dataImputChart.html", {'obj': obj})
    else:
        return HttpResponse("No tienes permiso para acceder a esta página.")

def get_dtColumn_imput(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Investigador":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:
            pkFinca = request.GET.get('finca')
            obj = DataClimImputation.objects.filter(api_parameters_finca=pkFinca)

            if obj.exists():
                response_data = {'allsky_sfc_sw_dwn' : 'allsky_sfc_sw_dwn', 
                             'clrsky_sfc_sw_dwn' : 'clrsky_sfc_sw_dwn', 
                             't2m_max' : 't2m_max',
                             't2m_min' : 't2m_min', 
                             't2mdew' : 't2mdew', 
                             'prectotcorr' : 'prectotcorr', 
                             'rh2m' : 'rh2m', 
                             'ws2m' : 'ws2m'}
                return JsonResponse(response_data)
            else:            
                return JsonResponse({'error': 'No existen valores imputados, debe ingresar a seleccionar los metodos de inputación para cada columna.'}, status=400)
        else:
            return JsonResponse({'error': 'La solicitud no es valida.'}, status=400)
    else:
        return JsonResponse({'error':'No tienes permiso para acceder a esta información.'})

def get_column_dataNasa(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Investigador":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:
            pkFinca = request.GET.get('finca')
            column = request.GET.get('column')
            current_year = datetime.now().year

            #data imputation
            objImputation = DataClimImputation.objects.filter(api_parameters_finca=pkFinca, date__year=current_year).values('date', column)
            max_valueImpt = DataClimImputation.objects.filter(api_parameters_finca=pkFinca).aggregate(max_value=Max('date'), min_value=Min('date'))
            valor_maximoImpt = max_valueImpt['max_value']
            valor_minimoImpt = max_valueImpt['min_value']

            #data nasa
            objClim = DataApiNasa.objects.filter(api_parameters_finca=pkFinca, date__year=current_year).values('date', column)
            
            datesImpt = []
            datesClim = []
            columnsImpt = []
            columnsClim = []

            if objImputation.exists():

                for item in objImputation:
                    datesImpt.append(item['date'])
                    columnsImpt.append(item[column])
            else:
                response_data['state'] = "ERROR"
                response_data['message'] = "No existen valores imputados, debe ingresar a seleccionar los metodos de inputación para cada columna."
                return JsonResponse(response_data, status=400)

            if objClim.exists():

                for item in objClim:
                    datesClim.append(item['date'])
                    columnsClim.append(item[column])
            
            response_data['state'] = "OK"
            response_data['message'] = ""    
            response_data['dateImpt'] = datesImpt
            response_data['columnImpt'] = columnsImpt
            response_data['value_max_date_impt'] = [valor_maximoImpt]
            response_data['value_min_date_impt'] = [valor_minimoImpt]
            response_data['dateClim'] = datesClim
            response_data['columnClim'] = columnsClim

            return JsonResponse(response_data)
        else:
            response_data['state'] = "ERROR"
            response_data['message'] = "La solicitud no es valida."
            return JsonResponse(response_data, status=400)
    else:
        response_data['state'] = "ERROR"
        response_data['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(response_data, status=400)


def get_data_rangeImput(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Investigador":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:
            pkFinca = request.GET.get('finca')
            column = request.GET.get('column')
            dateStart = datetime.strptime(request.GET.get('inputDateStart'), '%d/%m/%Y').strftime('%Y-%m-%d')
            dateLast = datetime.strptime(request.GET.get('inputDateLast'), '%d/%m/%Y').strftime('%Y-%m-%d')

            #data imputation
            objImputation = DataClimImputation.objects.filter(Q(api_parameters_finca=pkFinca) & 
                                                            Q(date__gte=dateStart) & 
                                                            Q(date__lte=dateLast)).values('date', column)
            
            #data nasa
            objClim = DataApiNasa.objects.filter(Q(api_parameters_finca=pkFinca) & 
                                                Q(date__gte=dateStart) & 
                                                Q(date__lte=dateLast)).values('date', column)
            
            datesImpt = []
            datesClim = []
            columnsImpt = []
            columnsClim = []

            if objImputation.exists():

                for item in objImputation:
                    datesImpt.append(item['date'])
                    columnsImpt.append(item[column])
            else:
                response_data['state'] = "ERROR"
                response_data['message'] = "No existen valores imputados, debe ingresar a seleccionar los metodos de inputación para cada columna."
                return JsonResponse(response_data, status=400)

            if objClim.exists():

                for item in objClim:
                    datesClim.append(item['date'])
                    columnsClim.append(item[column])
            
            response_data['state'] = "OK"
            response_data['message'] = ""    
            response_data['dateImpt'] = datesImpt
            response_data['columnImpt'] = columnsImpt
            response_data['dateClim'] = datesClim
            response_data['columnClim'] = columnsClim

            return JsonResponse(response_data)
        else:
            response_data['state'] = "ERROR"
            response_data['message'] = "La solicitud no es valida."
            return JsonResponse(response_data, status=400)
    else:
        response_data['state'] = "ERROR"
        response_data['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(response_data, status=400)


#End script TypeImpFieldDataClimaListView
#-----------------------------------------------------------------------------------------------------------------------------
#Start script ParamDeterministicModel
def get_elevation(lat, long):
    query = f'https://api.open-elevation.com/api/v1/lookup?locations={lat},{long}'
    response = requests.get(query).json() 
    return response

class CustomError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ParamDeterministicModelListView(LoginRequiredMixin, ListView):
    model = ParamDeterministicModel
    template_name = 'researcher/param_detr_model_list.html'
    context_object_name = 'paramDeterministicModel'

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class ParamDeterministicModelCreateView(LoginRequiredMixin, CreateView):
    form_class = ParamDeterministicModelForm
    template_name = 'researcher/param_detr_model_add.html' 

    def get_success_url(self):
        return reverse_lazy('paramDeterministicModel-create')


    def form_valid(self, form):     
        instance = form.save(commit=False)
        try:
            pkFinca = instance.finca.pk
        except ParamDeterministicModel.finca.RelatedObjectDoesNotExist:
            messages.error(self.request, 'No existe finca seleccionada.')
            #form.add_error(None, 'Error')
            return self.form_invalid(form)
        
        name_finca = None
        latitude = None
        longitude = None
        altitude = None
        
        try:
            if pkFinca:
                finca = Finca.objects.get(pk=pkFinca)      
                name_finca = finca.name    
                latitude = finca.latitud
                longitude = finca.longitud 

                result = get_elevation(latitude, longitude)
                altitude = result['results'][0]['elevation']
                if (not(altitude)):
                    raise CustomError("El API de altitud no retorno ningun resultado.")
                
        except Finca.DoesNotExist:
            form.add_error('finca', 'No la finca seleccionada.')
            return self.form_invalid(form)
        except CustomError as e:
            form.add_error('finca', e.message)
            return self.form_invalid(form)

        instance.altitude = altitude

        try:
            df = import_data_clim(pkFinca, 179)
        except Exception as e:
            messages.error(self.request, 'Ocurrio un error al traer los datos imputados: {}'.format(e))
            return self.form_invalid(form)

        #print(df)       
        try:
            deterministic_model = main_model_deterministic(altitude, df)
        except Exception as e:
            messages.error(self.request, 'Ocurrio un error al calcular el modelo deterministico: {}'.format(e))
            return self.form_invalid(form)
        data_df_objects = []
        instance.save()
        
        for index, row in deterministic_model.iterrows():
            data_df_objects.append(
                DeterministicModel(
                    param_deterministic=instance,
                    time=row['Time'],
                    etc=row['ETC'],
                    irrigation=row['Irrigation'],
                    draining=row['Draining'],
                    depletion=row['Depletion'],
                    paw=row['PAW'],
                    f_water=row['f_water'],
                    heat_stress_surplus=row['Heat_Stress_Surplus'],
                    heat_stress_slack=row['Heat_Stress_Slack'],
                    water_excess=row['Water_Excess'],
                    water_optimal=row['Water_Optimal'],
                    objective_value=row['Objective_Value'],
                )
            )
        DeterministicModel.objects.bulk_create(data_df_objects) 
        
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class DeterministicListView(LoginRequiredMixin, ListView):
    model = DeterministicModel
    template_name = 'researcher/deter_model_list.html'
    context_object_name = 'deterministicModel'

    def get_queryset(self):
        id_filtrado = self.kwargs['id_filtrado']  # Obtener el ID filtrado desde la UR
        queryset = DeterministicModel.objects.filter(param_deterministic=id_filtrado)
        return queryset

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class ParamDeterministicModelDeleteView(DeleteView):
    model = ParamDeterministicModel
    success_url = 'researcher/deterministicModel_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.finca
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                obj = ParamDeterministicModel.objects.get(finca=id)
            except ParamDeterministicModel.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Modelo determinista no encontrado.', 'type':'delete'})
            
            try:
                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 
                    return JsonResponse({'status': 'success', 'message': 'Los datos del modelo determinista ({}) de la finca de prueba: {}, fueron eliminados correctamente.'.format(id, obj.finca.name), 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar el modelo determinista.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar el modelo determinista porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})


#End script ParamDeterministicModel
#-----------------------------------------------------------------------------------------------------------------------------
#Start script IterativeModelling
class IterativeModellingListView(LoginRequiredMixin, ListView):
    model = IterativeModelling
    template_name = 'researcher/iterative_modelling_list.html'
    context_object_name = 'iterativeModelling'

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class IterativeModellingCreateView(LoginRequiredMixin, CreateView):
    form_class = IterativeModellingForm
    template_name = 'researcher/iterative_modelling_add.html' 

    def get_success_url(self):
        return reverse_lazy('iterativeModelling-create')


    def form_valid(self, form):     
        instance = form.save(commit=False)
        try:
            pkFinca = instance.finca.pk
        except IterativeModelling.finca.RelatedObjectDoesNotExist:
            messages.error(self.request, 'No existe finca seleccionada.')
            #form.add_error(None, 'Error')
            return self.form_invalid(form)
        
        name_finca = None
        
        try:
            if pkFinca:
                finca = Finca.objects.get(pk=pkFinca)      
                name_finca = finca.name    
        except Finca.DoesNotExist:
            form.add_error('finca', 'No existe la finca seleccionada.')
            return self.form_invalid(form)

        try:
            df = import_data_clim(pkFinca, 179)
        except Exception as e:
            messages.error(self.request, 'Ocurrio un error al traer los datos imputados: {}'.format(e))
            return self.form_invalid(form)

        #print(df)       
        try:
            selected_model,power,normal_params,normality_met = iterative_modeling(
                                                                                    pd.to_numeric(df[instance.columns_api_nasa.name.lower()]), 
                                                                                    instance.max_p, 
                                                                                    instance.max_q, 
                                                                                    instance.max_iterations, 
                                                                                    instance.n_neighbors,
                                                                                    float(instance.contamination)
                                                                                )
        except Exception as e:
            messages.error(self.request, 'Ocurrio un error al calcular el modelo iterativo: {}'.format(e))
            return self.form_invalid(form)
        
        mean = 0.0
        st_d = 0.0
        if normality_met:
            fig_diagnostics = selected_model.plot_diagnostics(figsize=(10, 10))
            buf_diagnostics = io.BytesIO()
            plt.savefig(buf_diagnostics, format='png')
            plt.close(fig_diagnostics)
            buf_diagnostics.seek(0)
            diagnostics_img_base64 = base64.b64encode(buf_diagnostics.read()).decode('utf-8')

            residuals = selected_model.resid()

            mean, st_d = normal_params if normal_params else (np.nan, np.nan)

            fig_residuals, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
            sns.histplot(residuals, kde=True, stat='density', ax=ax1)
            ax1.set_title('Residuals Density')
            ax1.set_xlabel('Residuals')
            ax1.set_ylabel('Density')

            if normal_params:
                x = np.linspace(mean - 3*st_d, mean + 3*st_d, 100)
                p = norm.pdf(x, mean, st_d)
                ax1.plot(x, p, color='red')

            sns.ecdfplot(residuals, ax=ax2)
            ax2.set_title('Cumulative Distribution of Residuals')
            ax2.set_xlabel('Residuals')
            ax2.set_ylabel('Cumulative Probability')
            plt.tight_layout()
        
            buf_residuals = io.BytesIO()
            plt.savefig(buf_residuals, format='png')
            plt.close(fig_residuals)
            buf_residuals.seek(0)
            residuals_img_base64 = base64.b64encode(buf_residuals.read()).decode('utf-8')
            
            instance.diagnostics_image = diagnostics_img_base64.encode('utf-8')
            instance.residuals_img = residuals_img_base64.encode('utf-8')

        instance.selected_model = pickle.dumps(selected_model)
        instance.power = power
        instance.mean = mean
        instance.st_d = st_d
        instance.save()
            
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

def get_data_iterative_modelling(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Investigador":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:
            pkFinca = request.GET.get('idFinca')
            idIterativeModelling = request.GET.get('idModelling')

            finca_exists = True
            try:
                if pkFinca:
                    finca = Finca.objects.get(pk=pkFinca)      
                    name_finca = finca.name    
            except Finca.DoesNotExist:
                finca_exists = False
            
            if finca_exists:
                objIterativeModelling = IterativeModelling.objects.get(pk=idIterativeModelling, finca=pkFinca)
    
                if objIterativeModelling:
                    model = pickle.loads(objIterativeModelling.selected_model)
                else:
                    response_data['state'] = "ERROR"
                    response_data['message'] = "No existe el modelo para la finca ingresada. Debe ejecutar para poder consultar."
                    return JsonResponse(response_data, status=400)
                #print(model.summary())

                
                response_data['state'] = "SUCCESS"
                response_data['message'] = "OK"   
                response_data['data'] =  model.summary().as_text()

                return JsonResponse(response_data)
            else:
                response_data['state'] = "ERROR"
                response_data['message'] = "La finca ingresada no existe."
                return JsonResponse(response_data, status=400)
                
        else:
            response_data['state'] = "ERROR"
            response_data['message'] = "La solicitud no es valida."
            return JsonResponse(response_data, status=400)
    else:
        response_data['state'] = "ERROR"
        response_data['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(response_data, status=400)
    

def get_graph_iterative_modelling(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Investigador":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:
            pkFinca = request.GET.get('idFinca')
            idIterativeModelling = request.GET.get('idModelling')

            finca_exists = True
            try:
                if pkFinca:
                    finca = Finca.objects.get(pk=pkFinca)      
                    name_finca = finca.name    
            except Finca.DoesNotExist:
                finca_exists = False
            
            if finca_exists:
                objIterativeModelling = IterativeModelling.objects.get(pk=idIterativeModelling, finca=pkFinca)
    
                if objIterativeModelling:
                    if objIterativeModelling.diagnostics_image and objIterativeModelling.residuals_img:
                        imgModel = objIterativeModelling.diagnostics_image.decode('utf-8')
                        imgResidualModel = objIterativeModelling.residuals_img.decode('utf-8')
                    else:
                        response_data['state'] = "ERROR"
                        response_data['message'] = "No existe grafico para el modelo ingresado."
                        return JsonResponse(response_data)
                else:
                    response_data['state'] = "ERROR"
                    response_data['message'] = "No existe el modelo para la finca ingresada. Debe ejecutar para poder consultar."
                    return JsonResponse(response_data, status=400)
                                
                response_data['state'] = "SUCCESS"
                response_data['message'] = "OK"   
                response_data['data'] =  [imgModel,imgResidualModel]

                return JsonResponse(response_data)
            else:
                response_data['state'] = "ERROR"
                response_data['message'] = "La finca ingresada no existe."
                return JsonResponse(response_data, status=400)
                
        else:
            response_data['state'] = "ERROR"
            response_data['message'] = "La solicitud no es valida."
            return JsonResponse(response_data, status=400)
    else:
        response_data['state'] = "ERROR"
        response_data['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(response_data, status=400)
    

class IterativeModellingDeleteView(DeleteView):
    model = IterativeModelling
    success_url = 'researcher/iterativeModelling_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.id
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                obj = IterativeModelling.objects.get(id=id)
            except IterativeModelling.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Modelo iterativo no encontrado.', 'type':'delete'})
            
            try:
                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 

                    return JsonResponse({'status': 'success', 'message': 'Los datos del modelo iterativo ({}) de la finca de prueba: {}, fueron eliminados correctamente.'.format(id, obj.finca.name), 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar el modelo iterativo.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar el modelo iterativo porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})
        

#End script IterativeModelling
#-----------------------------------------------------------------------------------------------------------------------------
#Start script ForecastScenarios

class ForecastScenariosListView(LoginRequiredMixin, ListView):
    model = ForecastScenarios
    template_name = 'researcher/forecast_scenarios_list.html'
    context_object_name = 'forecastScenarios'

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class ForecastScenariosCreateView(LoginRequiredMixin, CreateView):
    form_class = ForecastScenariosForm
    template_name = 'researcher/forecastScenarios_add.html' 

    def get_success_url(self):
        return reverse_lazy('forecastScenarios-create')


    def form_valid(self, form):     
        instance = form.save(commit=False)
        
        try:
            pkIterModel = instance.cod_modelo_iter.pk
        except ForecastScenarios.cod_modelo_iter.RelatedObjectDoesNotExist:
            messages.error(self.request, 'No existe modelo iterativo seleccionado.')
            return self.form_invalid(form)
        
        try:
            iterative_modelling = IterativeModelling.objects.get(pk=pkIterModel)
            power_modelling = iterative_modelling.power
            mean_modelling = iterative_modelling.mean
            st_d_modelling = iterative_modelling.st_d
        except IterativeModelling.DoesNotExist:
            form.add_error('cod_modelo_iter', 'No existe el modelo iterativo, debe ejecutarlo para esta finca antes.')
            return self.form_invalid(form)

        selected_model = pickle.loads(iterative_modelling.selected_model)

        try:
            forecasts_df = forecast_scenarios(selected_model, instance.steps, instance.n_scenarios, power_modelling, instance.alpha, mean_modelling, st_d_modelling)

            #forecasts_df = forecast_scenarios(selected_model)
        except Exception as e:
            messages.error(self.request, 'Ocurrio un error al ejecutar los escenarios: {}'.format(e))
            return self.form_invalid(form)
        
        instance.data_forecasts = forecasts_df.to_json()

        fig_forecasts = plt.figure(figsize=(10, 6))
        for i in range(instance.n_scenarios):
            plt.plot(forecasts_df.index, forecasts_df.iloc[:, i], color='blue', alpha=0.05)
        plt.title('Forecast Scenarios')
        plt.xlabel('Time Steps Ahead')
        plt.ylabel('Forecast Value')

        buf_forecasts = io.BytesIO()
        plt.savefig(buf_forecasts, format='png')
        plt.close(fig_forecasts)
        buf_forecasts.seek(0)
        forecasts_img_base64 = base64.b64encode(buf_forecasts.read()).decode('utf-8')

        instance.forecast_image = forecasts_img_base64.encode('utf-8')
        instance.save()
            
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

def get_graph_forecast_scenarios(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Investigador":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:
            idIterMol = request.GET.get('idIterMol')
            idForecastScenarios = request.GET.get('idForecastScenarios')

            finca_exists = True
            try:
                if idIterMol:
                    finca = IterativeModelling.objects.get(pk=idIterMol) 
            except IterativeModelling.DoesNotExist:
                finca_exists = False
            
            if finca_exists:
                objForecastScenarios = ForecastScenarios.objects.get(pk=idForecastScenarios, cod_modelo_iter=idIterMol)
    
                if objForecastScenarios:
                    if objForecastScenarios.forecast_image:
                        imgForecastScenarios = objForecastScenarios.forecast_image.decode('utf-8')
                    else:
                        response_data['state'] = "ERROR"
                        response_data['message'] = "No existe grafico para el modelo ingresado."
                        return JsonResponse(response_data)
                else:
                    response_data['state'] = "ERROR"
                    response_data['message'] = "No existe escenarios generados para la finca ingresada. Debe ejecutar para poder consultar."
                    return JsonResponse(response_data, status=400)
                                
                response_data['state'] = "SUCCESS"
                response_data['message'] = "OK"   
                response_data['data'] = imgForecastScenarios

                return JsonResponse(response_data)
            else:
                response_data['state'] = "ERROR"
                response_data['message'] = "La finca ingresada no existe."
                return JsonResponse(response_data, status=400)
                
        else:
            response_data['state'] = "ERROR"
            response_data['message'] = "La solicitud no es valida."
            return JsonResponse(response_data, status=400)
    else:
        response_data['state'] = "ERROR"
        response_data['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(response_data, status=400)


class ForecastScenariosDeleteView(DeleteView):
    model = ForecastScenarios
    success_url = 'researcher/forecastScenarios_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.id
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                obj = ForecastScenarios.objects.get(id=id)
            except ForecastScenarios.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Modelo generador de escenarios no encontrado.', 'type':'delete'})
            
            try:
                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 
                    return JsonResponse({'status': 'success', 'message': 'Los datos del modelo generador de escenarios ({}) de la finca de prueba: {}, fueron eliminados correctamente.'.format(id,obj.cod_modelo_iter.finca.name), 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar el modelo generador de escenarios.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar el modelo generador de escenarios porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})
        
#End script ForecastScenarios
#-----------------------------------------------------------------------------------------------------------------------------
#Start script MergeScenarios

class MergeScenariosListView(LoginRequiredMixin, ListView):
    model = MergeScenarios
    template_name = 'researcher/mergeScenarios_list.html'
    context_object_name = 'mergeScenarios'

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class MergeScenariosCreateView(LoginRequiredMixin, CreateView):
    form_class = MergeScenariosForm
    template_name = 'researcher/mergeScenarios_add.html' 

    def get_success_url(self):
        return reverse_lazy('mergeScenarios-create')


    def form_valid(self, form):     
        instance = form.save(commit=False)
        
        try:
            cod_forecast_scen = instance.cod_forecast_scen.pk
        except MergeScenarios.cod_forecast_scen.RelatedObjectDoesNotExist:
            messages.error(self.request, 'No existe escenarios seleccionados.')
            return self.form_invalid(form)

        try:
            forecast_scenarios = ForecastScenarios.objects.get(pk=cod_forecast_scen)     
            forecast_data = forecast_scenarios.data_forecasts
        except ForecastScenarios.DoesNotExist:
            form.add_error('cod_forecast_scen', 'No existe el escenario generado, debe ejecutar el generador de escenarios para poder continuar.')
            return self.form_invalid(form)

        df_forecast = pd.read_json(forecast_data)

        try:
            final_columns, final_probs, merge_history = merge_scenarios(df_forecast, instance.q, instance.tol, instance.a)
        except Exception as e:
            messages.error(self.request, 'Ocurrio un error al ejecutar el selecionador de escenarios: {}'.format(e))
            return self.form_invalid(form)
        
        instance.final_columns = json.dumps(final_columns.tolist())
        instance.final_probs = json.dumps(final_probs)
        instance.merge_history = json.dumps(merge_history)


        plt.style.use('ggplot')
        df = df_forecast[final_columns]
        probabilities = dict(zip(final_columns, final_probs))
        labels=True

        try:
            # Check if the dataframe has the columns specified in the probabilities dictionary
            if probabilities is not None and not set(probabilities.keys()).issubset(df.columns):
                raise ValueError("Some columns specified in probabilities are not in the dataframe")
        except Exception as e:
            messages.error(self.request, e)
            return self.form_invalid(form)

        # Calculate the mean of each column
        means = df.mean()

        # Normalize the means to [0, 1] for color mapping
        normalized_means = (means - means.min()) / (means.max() - means.min())

        # Create a color palette ranging from green to yellow to red
        colors = sns.color_palette("RdYlGn", len(df.columns))

        # Sort columns by mean values for color assignment
        sorted_columns = means.sort_values().index
        
        plt.figure(figsize=(10, 6))

        # Plot each column with its corresponding color and added transparency
        for col in sorted_columns:
            label_text = f"{col} (P={probabilities[col]:.2f})" if labels and probabilities and col in probabilities else col
            plt.plot(df.index, df[col], label=label_text,
                    color=colors[int(normalized_means[col] * (len(colors) - 1))],
                    alpha=0.4)  # Setting transparency

        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title('Time Series Plot')

        if labels:
            plt.legend(title="Series Legend", bbox_to_anchor=(1.05, 1), loc='upper left')

        #plt.show()
        buf_merge = io.BytesIO()
        plt.savefig(buf_merge, format='png', bbox_inches='tight')
        buf_merge.seek(0)
        merge_img_base64 = base64.b64encode(buf_merge.read()).decode('utf-8')
        buf_merge.close()

        instance.merge_image = merge_img_base64.encode('utf-8')

        instance.save()
   
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


def get_graph_merge_scenarios(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Investigador":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:
            idForecScen = request.GET.get('idforecscen')
            idMergeScenarios = request.GET.get('idMergeScenarios')

            idForecScen_exists = True
            try:
                if idForecScen:
                    forecastScenarios = ForecastScenarios.objects.get(pk=idForecScen)
            except ForecastScenarios.DoesNotExist:
                idForecScen_exists = False
            
            if idForecScen_exists:
                objMergeScenarios = MergeScenarios.objects.get(pk=idMergeScenarios, cod_forecast_scen=idForecScen)
    
                if objMergeScenarios:
                    if objMergeScenarios.merge_image:
                        imgMergeScenarios = objMergeScenarios.merge_image.decode('utf-8')
                    else:
                        response_data['state'] = "ERROR"
                        response_data['message'] = "No existe grafico para el modelo ingresado."
                        return JsonResponse(response_data)
                else:
                    response_data['state'] = "ERROR"
                    response_data['message'] = "No existe escenarios seleccionados para la finca ingresada. Debe ejecutar el proceso de selección de escenarios para poder consultar la gráfica."
                    return JsonResponse(response_data, status=400)
                                
                response_data['state'] = "SUCCESS"
                response_data['message'] = "OK"   
                response_data['data'] = imgMergeScenarios

                return JsonResponse(response_data)
            else:
                response_data['state'] = "ERROR"
                response_data['message'] = "La finca ingresada no existe."
                return JsonResponse(response_data, status=400)
                
        else:
            response_data['state'] = "ERROR"
            response_data['message'] = "La solicitud no es valida."
            return JsonResponse(response_data, status=400)
    else:
        response_data['state'] = "ERROR"
        response_data['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(response_data, status=400)
    

class MergeScenariosDeleteView(DeleteView):
    model = MergeScenarios
    success_url = 'researcher/model/mergeScenarios_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.id
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                obj = MergeScenarios.objects.get(id=id)
            except MergeScenarios.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Modelo seleccionado no encontrado.', 'type':'delete'})
            
            try:
                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 
                    return JsonResponse({'status': 'success', 'message': 'Los datos del modelo de selección ({}) de la finca de prueba: {}, fueron eliminados correctamente.'.format(id,obj.cod_forecast_scen.cod_modelo_iter.finca.name), 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar el modelo de selección.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar el modelo de selección porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})
    
#End script MergeScenarios
#-----------------------------------------------------------------------------------------------------------------------------
#Start script TwoStageModel

class TwoStageModelListView(LoginRequiredMixin, ListView):
    model = TwoStageModel
    template_name = 'researcher/twoStageModel_list.html'
    context_object_name = 'twoStageModel'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Transformar los datos de cada instancia
        transformed_data = []
        for instance in context['twoStageModel']:
            data = json.loads(instance.Irrigation_and_drainage)

            transformed_data.append({
                'pk': instance.pk,
                'finca': instance.finca,
                'data': data,
            })
        
        # Añadir los datos transformados al contexto
        context['transformed_data'] = transformed_data
        return context

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


def query_column(pkFinca, column, form, invalid_form):
    iterative_modelling = IterativeModelling.objects.filter(finca=pkFinca, columns_api_nasa__name=column).order_by('-pk').first()

    if iterative_modelling:
        forecastScenarios = ForecastScenarios.objects.filter(cod_modelo_iter=iterative_modelling).order_by('-pk').first()
        if forecastScenarios:
            mergeScenarios = MergeScenarios.objects.filter(cod_forecast_scen=forecastScenarios).order_by('-pk').first()
            if not mergeScenarios:
                form.add_error('finca', 'No existe el escenarios seleccionados para la columna {}, debe ejecutar el proceso de selección de escenarios para esta columna.'.format(column))
                return invalid_form, None, None
            else:
                return forecastScenarios.data_forecasts, mergeScenarios.final_columns, mergeScenarios.final_probs
        else:
            form.add_error('finca', 'No existe generador de escenarios para la columna {}, debe ejecutar el proceso de generar escenarios para esta columna.'.format(column))
            return invalid_form, None, None
    else:
        form.add_error('finca', 'No existe modelo iterativo para la columna {}, debe ejecutar el proceso de modelo iterativo para esta columna.'.format(column))
        return invalid_form, None, None


class TwoStageModelCreateView(LoginRequiredMixin, CreateView):
    form_class = TwoStageModelForm
    template_name = 'researcher/twoStageModel_add.html' 

    def get_success_url(self):
        return reverse_lazy('twoStageModel-create')


    def form_valid(self, form):     
        instance = form.save(commit=False)
        pkFinca = instance.finca.pk

        try:
            if pkFinca:
                finca = Finca.objects.get(pk=pkFinca)      
        except Finca.DoesNotExist:
            form.add_error('finca', 'No existe la finca seleccionada.')
            return self.form_invalid(form)
        
        #fore_sce_dt_allsky, merg_sce_colum_allsky, merg_sce_probs_allsky = query_column(pkFinca,'allsky_sfc_sw_dwn',form, self.form_invalid(form)) 
        #fore_sce_dt_clrsky, merg_sce_colum_clrsky, merg_sce_probs_clrsky = query_column(pkFinca,'clrsky_sfc_sw_dwn',form, self.form_invalid(form)) 
        #fore_sce_dt_t2m_max, merg_sce_colum_t2m_max, merg_sce_probs_t2m_max = query_column(pkFinca,'t2m_max',form, self.form_invalid(form)) 
        #fore_sce_dt_t2m_min, merg_sce_colum_t2m_min, merg_sce_probs_t2m_min = query_column(pkFinca,'t2m_min',form, self.form_invalid(form)) 
        #fore_sce_dt_t2mdew, merg_sce_colum_t2mdew, merg_sce_probs_t2mdew = query_column(pkFinca,'t2mdew',form, self.form_invalid(form)) 
        fore_sce_dt_prect, merg_sce_colum_prect, merg_sce_probs_prect = query_column(pkFinca,'prectotcorr',form, self.form_invalid(form)) 
        #fore_sce_dt_rh2m, merg_sce_colum_rh2m, merg_sce_probs_rh2m = query_column(pkFinca,'rh2m',form, self.form_invalid(form))         
        #fore_sce_dt_ws2m, merg_sce_colum_ws2m, merg_sce_probs_ws2m = query_column(pkFinca,'ws2m',form, self.form_invalid(form))         

        if form.errors:
            return self.form_invalid(form)
        
        try:
            result = main(
                            pkFinca,
                            json.loads(fore_sce_dt_prect),
                            ast.literal_eval(merg_sce_colum_prect),
                            ast.literal_eval(merg_sce_probs_prect)
                        )
        except Exception as e:
            messages.error(self.request, 'Ocurrio un error al ejecutar el modelo de optimización: {}'.format(e))
            return self.form_invalid(form)
        

        instance.Irrigation_and_drainage = json.dumps(result)

        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(researcher_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class TwoStageModelDeleteView(DeleteView):
    model = TwoStageModel
    success_url = 'researcher/twoStageModel_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.id
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                obj = TwoStageModel.objects.get(id=id)
            except TwoStageModel.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Modelo de optimización no encontrado.', 'type':'delete'})
            
            try:
                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 
                    return JsonResponse({'status': 'success', 'message': 'Los datos del modelo de optimización ({}) de la finca de prueba: {}, fueron eliminados correctamente.'.format(id, obj.finca.name), 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar el modelo de optimización.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar el modelo de optimización porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})
    
#End script TwoStageModel
