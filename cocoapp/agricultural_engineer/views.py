from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Max, Min, ProtectedError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, Http404
from .models import *
from .forms import APIParameterNasaFincaForm
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

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
import heapq

from django.utils.decorators import method_decorator
from researcher.models import *
from researcher.modelo.import_data_api import get_data
from researcher.modelo.imputation_date import imputation
from researcher.modelo.modelling import iterative_modeling
from researcher.modelo.data import import_data_clim
from researcher.modelo.forecast_scenarios import forecast_scenarios
from researcher.modelo.merge_scenarios import merge_scenarios
from researcher.modelo.two_stage_opti_model import main
from django.views.decorators.csrf import csrf_protect

# Create your views here.
def agricultural_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
                    pass
            except:
                raise Http404("No existe perfil asociado al usuario. Comuníquese con el administrador del sistema.")

            
            if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
                return view_func(request, *args, **kwargs)
            else:
                raise Http404("Usuario no tiene permisos suficientes.")               
            
        else:
            raise Http404("Usuario no autenticado.")
    return _wrapped_view


#-----------------------------------------------------------------------------------------------------------------------------
#Start script APIParameterNasaFinca

class APIParameterNasaFincaListView(ListView):
    model = APIParameterNasaFinca
    template_name = 'agricultural_engineer/api_parameter_nasa_finca_list.html'
    context_object_name = 'aPIParameterNasaFinca'

    @method_decorator(agricultural_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

def get_api_parameter_dt(request):
    context = {}

    if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
        if request.method == 'GET' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            data = request.GET

            draw = int(data.get("draw"))
            start = int(data.get("start"))
            length = int(data.get("length"))
            search = data.get("search[value]")

            registers = APIParameterNasaFinca.objects.all()

            if search:
                registers = registers.filter(
                    Q(finca__name__icontains=search) |
                    Q(latitud__icontains=search) |
                    Q(longitud__icontains=search) |
                    Q(longitude__icontains=search) |
                    Q(date_exceute__icontains=search) |
                    Q(date_start__icontains=search) |
                    Q(date_end__icontains=search)
                )
            
            recordsTotal = registers.count()

            context["draw"] = draw
            context["recordsTotal"] = recordsTotal
            context["recordsFiltered"] = recordsTotal

            reg = registers[start:start + length]
            paginator = Paginator(reg, length)

            try:
                obj = paginator.page(draw).object_list
            except PageNotAnInteger:
                obj = paginator.page(draw).object_list
            except EmptyPage:
                obj = paginator.page(paginator.num_pages).object_list
                

            datos = [
                {
                    "id": o.pk,
                    "finca": o.finca.name, 
                    "latitud": o.latitud, 
                    "longitud": o.longitud,
                    "date_exceute": o.date_exceute.strftime("%d/%b/%Y"), 
                    "date_start": o.date_start.strftime("%d/%b/%Y"), 
                    "date_end": o.date_end.strftime("%d/%b/%Y")
                } for o in obj
            ]

            context["datos"] = datos
            return JsonResponse(context, safe=False)
        else:
            context["draw"] = 0
            context["recordsTotal"] = 0
            context["recordsFiltered"] = 0
            return JsonResponse(context, status=400, safe=False)
    else:
        context['state'] = "ERROR"
        context['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(context, status=400)
    

class APIParameterNasaFincaCreateView(LoginRequiredMixin, CreateView):
    form_class = APIParameterNasaFincaForm
    template_name = 'agricultural_engineer/api_parameter_nasa_finca_add.html'

    def get_success_url(self):
        return reverse_lazy('api_parameter_nasa_finca-create')

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
                    DataApiNasaFinca(
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
            DataApiNasaFinca.objects.bulk_create(data_api_nasa_objects) # Usar bulk_create para guardar todos los objetos a la vez
        except Exception as e:
            messages.error(self.request, "Ocurrio un error en el aplicativo: {}".format(e))
            return self.form_invalid(form)
        
        #start imputation
        try:
            obj = TypeImpFieldDataClima.objects.latest('pk')  
        except ObjectDoesNotExist:
            form.add_error('finca', 'No existe información configurada por el investigar para imputación de datos: {}}'.format(e))
            return self.form_invalid(form)


        try:
            df_result = imputation('ing_agrnomo',
                                    pkFinca, 
                                    instance.finca.name, 
                                    obj.allsky_sfc_sw_dwn,
                                    obj.clrsky_sfc_sw_dwn,
                                    obj.t2m_max,
                                    obj.t2m_min,
                                    obj.t2mdew,
                                    obj.prectotcorr,
                                    obj.rh2m,
                                    obj.ws2m)  
        except Exception as e:
            form.add_error('finca', '{}'.format(e))
            return self.form_invalid(form)
               
        data_df_objects = []
        try:
            for index, row in df_result.iterrows():
                data_df_objects.append(
                    DataApiNasaImputation(
                        api_parameters_finca=instance,
                        type_imp_data=obj,
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
            DataApiNasaImputation.objects.bulk_create(data_df_objects) 
        except Exception as e:
            messages.error(self.request, 'Ocurrio al guardar los datos imputados: {}'.format(e))
            return self.form_invalid(form)
        #end imputation

        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(agricultural_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class DataClimFincaListView(LoginRequiredMixin, ListView):
    model = APIParameterNasaFinca
    template_name = 'agricultural_engineer/data_clim_finca_list.html'
    context_object_name = 'aPIParameterNasaFinca'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id_filtrado = self.kwargs['id_filtrado']
        finca_obj = APIParameterNasaFinca.objects.get(pk=id_filtrado)
        pk_twoStage = ''
        data = ''
        pk_finca = ''

        if finca_obj:
            pk_finca = finca_obj.pk
            best_pronostic_model_obj = BeastPronosticModel.objects.filter(finca = finca_obj.finca).first()
            two_stage_finca_model_obj = TwoStageFincaModel.objects.filter(finca = finca_obj.finca).first()

            if two_stage_finca_model_obj:
                pk_twoStage = two_stage_finca_model_obj.pk
                data = json.loads(two_stage_finca_model_obj.Irrigation_and_drainage)

        context['pk_finca'] = pk_finca
        context['pronostic_model_obj'] = best_pronostic_model_obj
        context['pk_two_stage_finca'] = pk_twoStage
        context['two_stage_finca_model_obj'] = data

        return context

    def get_queryset(self):
        id_filtrado = self.kwargs['id_filtrado']  # Obtener el ID filtrado desde la UR
        queryset = APIParameterNasaFinca.objects.filter(pk=id_filtrado)
        return queryset

    @method_decorator(agricultural_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class APIParameterNasaFincaDeleteView(DeleteView):
    model = APIParameterNasaFinca
    success_url = 'agricultural_engineer/data_clim_finca_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.pk
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                if id:
                    finca = Finca.objects.get(pk=id)      
            except Finca.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Finca no encontrada.', 'type':'delete'})
            
            try:
                obj = APIParameterNasaFinca.objects.get(finca=finca)
            except APIParameterNasaFinca.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Modelo de optimización no encontrado.', 'type':'delete'})
            
            try:
                data_Api_nasa_finca_obj = DataApiNasaFinca.objects.filter(api_parameters_finca=obj).delete()
                pronostic_model_obj = PronosticModel.objects.filter(finca=finca).delete()
                beast_pronostic_obj = BeastPronosticModel.objects.filter(finca=finca).delete()
                two_stage_model_obj = TwoStageFincaModel.objects.filter(finca=finca).delete()

                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 
                    return JsonResponse({'status': 'success', 'message': 'Los datos del modelo de optimización ({}) de la finca de prueba: {}, fueron eliminados correctamente.'.format(id, obj.finca.name), 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar el modelo de optimización.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar el modelo de optimización porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})
    

def get_api_imputation_dt(request):
    context = {}

    if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
        if request.method == 'GET' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            data = request.GET

            draw = int(data.get("draw"))
            start = int(data.get("start"))
            length = int(data.get("length"))
            search = data.get("search[value]")
            param = int(data.get("param"))

            registers = DataApiNasaImputation.objects.filter(api_parameters_finca = param).order_by('-date')

            if search:
                registers = registers.filter(
                    Q(date__icontains=search) |
                    Q(allsky_sfc_sw_dwn__icontains=search) |
                    Q(clrsky_sfc_sw_dwn__icontains=search) |
                    Q(t2m_max__icontains=search) |
                    Q(t2m_min__icontains=search) |
                    Q(t2mdew__icontains=search) |
                    Q(prectotcorr__icontains=search) |
                    Q(rh2m__icontains=search) |
                    Q(ws2m__icontains=search)
                )
            
            recordsTotal = registers.count()

            context["draw"] = draw
            context["recordsTotal"] = recordsTotal
            context["recordsFiltered"] = recordsTotal

            reg = registers[start:start + length]
            paginator = Paginator(reg, length)

            try:
                obj = paginator.page(draw).object_list
            except PageNotAnInteger:
                obj = paginator.page(draw).object_list
            except EmptyPage:
                obj = paginator.page(paginator.num_pages).object_list
                

            datos = [
                {
                    "date": o.date,
                    "allsky_sfc_sw_dwn": o.allsky_sfc_sw_dwn, 
                    "clrsky_sfc_sw_dwn": o.clrsky_sfc_sw_dwn, 
                    "t2m_max": o.t2m_max,
                    "t2m_min": o.t2m_min, 
                    "t2mdew": o.t2mdew, 
                    "prectotcorr": o.prectotcorr,
                    "rh2m": o.rh2m,
                    "ws2m": o.ws2m,
                } for o in obj
            ]

            context["datos"] = datos
            return JsonResponse(context, safe=False)
        else:
            context["draw"] = 0
            context["recordsTotal"] = 0
            context["recordsFiltered"] = 0
            return JsonResponse(context, status=400, safe=False)
    else:
        context['state'] = "ERROR"
        context['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(context, status=400)
    

@csrf_protect
def delete_beast_pronostic(request, pk):
    context = {}

    if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
        if request.method == 'POST' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':

            try:
                if pk:
                    finca = Finca.objects.get(pk=pk)      
            except Finca.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Finca no encontrada.', 'type':'delete'})
            
            pronostic_model_obj = PronosticModel.objects.filter(finca=finca)
            beast_pronostic_obj = BeastPronosticModel.objects.filter(finca=finca)
            two_stage_model_obj = TwoStageFincaModel.objects.filter(finca=finca)

            if pronostic_model_obj.exists():
               pronostic_model_obj.delete()
               beast_pronostic_obj.delete()
               two_stage_model_obj.delete()
               return JsonResponse({'status': 'success', 'message': 'Los datos de modelo se eliminaron correctamente.', 'type':'delete'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Modelo de optimización no encontrado para la finca.', 'type':'delete'})
        else:
            context = {'status': 'error', 'message': 'Solicitud no valida.', 'type': 'delete'}
            return JsonResponse(context)
    else:
        context['state'] = "error"
        context['message'] = "No tienes permiso para acceder a esta información."
        context['type'] ='delete'
        return JsonResponse(context, status=400)

#End script APIParameterNasaFinca
#-----------------------------------------------------------------------------------------------------------------------------
#Start script PronosticModel

@csrf_protect
def set_pronostic_model(request):
    context = {}

    if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
        if request.method == 'POST' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            data = request.POST
            pkFinca = int(data.get("finca"))
            #columns = ['allsky_sfc_sw_dwn', 'clrsky_sfc_sw_dwn', 't2m_max', 't2m_min', 't2mdew', 'prectotcorr', 'rh2m', 'ws2m']
            columns = ['prectotcorr']

            try:
                if pkFinca:
                    finca = Finca.objects.get(pk=pkFinca)    
            except Finca.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'No existe la finca seleccionada.', 'type': 'create'}) 

            final_df = pd.DataFrame()
            for i in columns:
                last_iter_modl = IterativeModelling.objects.filter(columns_api_nasa__name=i).order_by('-pk').first()
                
                if not last_iter_modl:
                    return JsonResponse({'status': 'error', 'message': 'No existe modelo iterativo, para la columna {}'.format(i), 'type': 'create'})
                
                last_forec_model = ForecastScenarios.objects.filter(cod_modelo_iter=last_iter_modl.pk).order_by('-pk').first()

                if not last_forec_model:
                    return JsonResponse({'status': 'error', 'message': 'No existe modelo generador de escenarios para la columna {}'.format(i), 'type': 'create'})
                         
                last_selct_model = MergeScenarios.objects.filter(cod_forecast_scen=last_forec_model.pk).order_by('-pk').first()

                if not last_selct_model:
                    return JsonResponse({'status': 'error', 'message': 'No existe selección de escenarios para la columna {}'.format(i), 'type': 'create'})
                
                
                try:
                    df = import_data_clim(pkFinca, 179, perfil='agricultural engineer')
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': 'Ocurrio un error al traer los datos imputados: {}'.format(e), 'type': 'create'}) 
                
                try:
                    selected_model,power,normal_params,normality_met = iterative_modeling(
                                                                                            pd.to_numeric(df[last_iter_modl.columns_api_nasa.name.lower()]), 
                                                                                            last_iter_modl.max_p, 
                                                                                            last_iter_modl.max_q, 
                                                                                            last_iter_modl.max_iterations, 
                                                                                            last_iter_modl.n_neighbors,
                                                                                            float(last_iter_modl.contamination)
                                                                                        )
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': 'Ocurrio un error al calcular el modelo iterativo: {}'.format(e), 'type': 'create'}) 
                
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

                try:
                    forecasts_df = forecast_scenarios(selected_model, last_forec_model.steps, last_forec_model.n_scenarios, power, last_forec_model.alpha, mean, st_d)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': 'Ocurrio un error al ejecutar los escenarios: {}'.format(e), 'type': 'create'}) 
                
                try:
                    final_columns, final_probs, merge_history = merge_scenarios(forecasts_df, last_selct_model.q, last_selct_model.tol, last_selct_model.a)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': 'Ocurrio un error al ejecutar el selecionador de escenarios: {}'.format(e), 'type': 'create'}) 
                
                if i == 'prectotcorr':
                    all_prectot = ['prectotcorr1', 'prectotcorr2', 'prectotcorr3']
                    tree_values = heapq.nlargest(3, final_probs)
                    index = [i for i, v in enumerate(final_probs) if v in tree_values]
                    values_select = [final_columns[i] for i in index]
                    
                    idx = 0
                    for column in values_select:
                        final_df[all_prectot[idx]] = forecasts_df[column]
                        idx +=1
                else:
                    fProbs_max_value = final_probs.index(max(final_probs))
                    fColumns = final_columns[fProbs_max_value]
                    selected_column = forecasts_df[fColumns]
                    
                    final_df[i] = selected_column

                
                nuevo_modelo = PronosticModel(
                    finca=finca,
                    columns_api_nasa=last_iter_modl.columns_api_nasa,
                    selected_model=pickle.dumps(selected_model),
                    power=power,
                    mean=mean,
                    st_d=st_d,
                    data_forecasts=forecasts_df.to_json(),
                    final_columns=json.dumps(final_columns.tolist()),
                    final_probs=json.dumps(final_probs),
                )
                
                nuevo_modelo.save()
            #end for

            final_df.reset_index(inplace=True)
            final_df.rename(columns={'index': 'Index'}, inplace=True)
            
            beast_pronostic = [
                BeastPronosticModel(
                    finca = finca,
                    dia=row['Index'],
                    allsky_sfc_sw_dwn=row['allsky_sfc_sw_dwn'] if 'allsky_sfc_sw_dwn' in final_df.columns else None,
                    clrsky_sfc_sw_dwn=row['clrsky_sfc_sw_dwn'] if 'clrsky_sfc_sw_dwn' in final_df.columns else None,
                    t2m_max=row['t2m_max'] if 't2m_max' in final_df.columns else None,
                    t2m_min=row['t2m_min'] if 't2m_min' in final_df.columns else None,
                    t2mdew=row['t2mdew'] if 't2mdew' in final_df.columns else None,
                    prectotcorr1=row['prectotcorr1'] if 'prectotcorr1' in final_df.columns else None,
                    prectotcorr2=row['prectotcorr2'] if 'prectotcorr2' in final_df.columns else None,
                    prectotcorr3=row['prectotcorr3'] if 'prectotcorr3' in final_df.columns else None,
                    rh2m=row['rh2m'] if 'rh2m' in final_df.columns else None,
                    ws2m=row['ws2m'] if 'ws2m' in final_df.columns else None
                ) for _, row in final_df.iterrows()
            ]

            BeastPronosticModel.objects.bulk_create(beast_pronostic)
            #selected_model = pickle.dumps(selected_model)

            context = {'status': 'success', 'message': 'ok', 'type': 'create'}
            return JsonResponse(context)
        else:
            context = {'status': 'error', 'message': 'Solicitud no valida.', 'type': 'create'}
            return JsonResponse(context)
    else:
        context['state'] = "error"
        context['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(context, status=400)
    

def get_pronostic_day_dt(request):
    context = {}

    if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
        if request.method == 'GET' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            data = request.GET

            draw = int(data.get("draw"))
            start = int(data.get("start"))
            length = int(data.get("length"))
            search = data.get("search[value]")
            param = int(data.get("param"))

            registers = BeastPronosticModel.objects.filter(finca = param).order_by('pk')

            if search:
                registers = registers.filter(
                    Q(dia__icontains=search) |
                    Q(allsky_sfc_sw_dwn__icontains=search) |
                    Q(clrsky_sfc_sw_dwn__icontains=search) |
                    Q(t2m_max__icontains=search) |
                    Q(t2m_min__icontains=search) |
                    Q(t2mdew__icontains=search) |
                    Q(prectotcorr1__icontains=search) |
                    Q(prectotcorr2__icontains=search) |
                    Q(prectotcorr3__icontains=search) |
                    Q(rh2m__icontains=search) |
                    Q(ws2m__icontains=search)
                )
            
            recordsTotal = registers.count()

            context["draw"] = draw
            context["recordsTotal"] = recordsTotal
            context["recordsFiltered"] = recordsTotal

            reg = registers[start:start + length]
            paginator = Paginator(reg, length)

            try:
                obj = paginator.page(draw).object_list
            except PageNotAnInteger:
                obj = paginator.page(draw).object_list
            except EmptyPage:
                obj = paginator.page(paginator.num_pages).object_list
                

            datos = [
                {
                    "dia": o.dia,
                    "allsky_sfc_sw_dwn": o.allsky_sfc_sw_dwn, 
                    "clrsky_sfc_sw_dwn": o.clrsky_sfc_sw_dwn, 
                    "t2m_max": o.t2m_max,
                    "t2m_min": o.t2m_min, 
                    "t2mdew": o.t2mdew, 
                    "prectotcorr1": o.prectotcorr1,
                    "prectotcorr2": o.prectotcorr2,
                    "prectotcorr3": o.prectotcorr3,
                    "rh2m": o.rh2m,
                    "ws2m": o.ws2m,
                } for o in obj
            ]

            context["datos"] = datos
            return JsonResponse(context, safe=False)
        else:
            context["draw"] = 0
            context["recordsTotal"] = 0
            context["recordsFiltered"] = 0
            return JsonResponse(context, status=400, safe=False)
    else:
        context['state'] = "ERROR"
        context['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(context, status=400)
    

def get_data_rangeImputAgri(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:
            pkFinca = request.GET.get('finca')
            column = request.GET.get('column')
            
            try:
                if request.GET.get('inputDateStart') == '' and request.GET.get('inputDateLast') == '':
                    objImputation = DataApiNasaImputation.objects.filter(api_parameters_finca=pkFinca).values('date', column)
                    max_valueImpt = DataApiNasaImputation.objects.filter(api_parameters_finca=pkFinca).aggregate(max_value=Max('date'), min_value=Min('date'))

                else:
                    dateStart = datetime.strptime(request.GET.get('inputDateStart'), '%d/%m/%Y').strftime('%Y-%m-%d')
                    dateLast = datetime.strptime(request.GET.get('inputDateLast'), '%d/%m/%Y').strftime('%Y-%m-%d')
                    #data imputation
                    objImputation = DataApiNasaImputation.objects.filter(Q(api_parameters_finca=pkFinca) & 
                                                                    Q(date__gte=dateStart) & 
                                                                    Q(date__lte=dateLast)).values('date', column)
                    max_valueImpt = DataApiNasaImputation.objects.filter(Q(api_parameters_finca=pkFinca) & 
                                                                    Q(date__gte=dateStart) & 
                                                                    Q(date__lte=dateLast)).aggregate(max_value=Max('date'), min_value=Min('date'))
            except Exception as error:
                response_data['state'] = "ERROR"
                response_data['message'] = "Ocurrio un error: {}".format(error)
                return JsonResponse(response_data, status=400)

            valor_maximoImpt = max_valueImpt['max_value']
            valor_minimoImpt = max_valueImpt['min_value']

            #objImputation = DataApiNasaImputation.objects.filter(api_parameters_finca=pkFinca).values('date', column)

                       
            datesImpt = []
            columnsImpt = []

            if objImputation.exists():

                for item in objImputation:
                    datesImpt.append(item['date'])
                    columnsImpt.append(item[column])
            else:
                response_data['state'] = "ERROR"
                response_data['message'] = "No existen valores imputados, debe ingresar a seleccionar los metodos de inputación para cada columna."
                return JsonResponse(response_data, status=400)
            
            response_data['state'] = "OK"
            response_data['message'] = ""    
            response_data['dateImpt'] = datesImpt
            response_data['value_max_date_impt'] = [valor_maximoImpt]
            response_data['value_min_date_impt'] = [valor_minimoImpt]
            response_data['columnImpt'] = columnsImpt

            return JsonResponse(response_data)
        else:
            response_data['state'] = "ERROR"
            response_data['message'] = "La solicitud no es valida."
            return JsonResponse(response_data, status=400)
    else:
        response_data['state'] = "ERROR"
        response_data['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(response_data, status=400)
    

def get_data_farmer_chart(request):
    response_data = {}    
    if request.user.userprofile.profile.profile == "Agricultor":
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if request.method == 'GET' and is_ajax:

            try:
                obj_finca = Finca.objects.filter(owner_name=request.user).first()

            except Finca.DoesNotExist:
                response_data['state'] = "ERROR"
                response_data['message'] = "No existen la finca."
                return JsonResponse(response_data)
                   
            
            try:
                obj_pronostic = PronosticModel.objects.filter(finca=obj_finca).values('final_probs')
                obj_beast_pronostic = BeastPronosticModel.objects.filter(finca=obj_finca).values('dia', 't2mdew', 'prectotcorr1', 'prectotcorr2', 'prectotcorr3')
            except Exception as error:
                response_data['state'] = "ERROR"
                response_data['message'] = "Ocurrio un error: {}".format(error)
                return JsonResponse(response_data)
            
            probs_prec = []
            if obj_pronostic.exists():
                for item in obj_pronostic:
                    probs_prec = [value * 100 for value in ast.literal_eval(item['final_probs'])]
            
            clm_dia = []
            clm_t2mdew = []
            clm_prectotcorr1 = []
            clm_prectotcorr2 = []
            clm_prectotcorr3 = []


            if obj_beast_pronostic.exists():

                for item in obj_beast_pronostic:
                    clm_dia.append(item['dia'])
                    clm_t2mdew.append(item['t2mdew'])
                    clm_prectotcorr1.append(item['prectotcorr1'])
                    clm_prectotcorr2.append(item['prectotcorr2'])
                    clm_prectotcorr3.append(item['prectotcorr3'])
            else:
                response_data['state'] = "ERROR"
                response_data['message'] = "No existen valores climatologícos para la finca."
                return JsonResponse(response_data)
            
            response_data['state'] = "OK"
            response_data['message'] = ""    
            response_data['dia'] = clm_dia
            response_data['tmp'] = clm_t2mdew
            response_data['prectotcorr1'] = clm_prectotcorr1
            response_data['prectotcorr2'] = clm_prectotcorr2
            response_data['prectotcorr3'] = clm_prectotcorr3
            response_data['probs_prec'] = probs_prec

            return JsonResponse(response_data)
        else:
            response_data['state'] = "ERROR"
            response_data['message'] = "La solicitud no es valida."
            return JsonResponse(response_data)
    else:
        response_data['state'] = "ERROR"
        response_data['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(response_data)


#End script PronosticModel
#-----------------------------------------------------------------------------------------------------------------------------
#Start script TwoStageFincaModel

def query_agric_column(pkFinca, column):
    # iterative_modelling = IterativeModelling.objects.filter(finca=pkFinca, columns_api_nasa__name=column).order_by('-pk').first()

    pronostic_model = PronosticModel.objects.filter(finca=pkFinca, columns_api_nasa__name=column).first()

    if pronostic_model:
        return {'response': 'OK', 
                'data_forecasts': pronostic_model.data_forecasts, 
                'final_columns': pronostic_model.final_columns,
                'final_probs': pronostic_model.final_probs}
    else:
        return {'response': 'ERROR', 'msg': 'No existe modelo para la finca y columna: {}'.format(column)}

@csrf_protect
def set_two_stage_model(request):
    context = {}

    if request.user.userprofile.profile.profile == "Ingeniero Agrónomo":
        if request.method == 'POST' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            data = request.POST
            pkFinca = int(data.get("finca"))

            try:
                if pkFinca:
                    finca = Finca.objects.get(pk=pkFinca)    
            except Finca.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'No existe la finca seleccionada.', 'type': 'create'}) 

            # response_allsky = query_agric_column(pkFinca,'allsky_sfc_sw_dwn') 
            # response_clrsky = query_agric_column(pkFinca,'clrsky_sfc_sw_dwn') 
            # response_t2m_max = query_agric_column(pkFinca,'t2m_max') 
            # response_t2m_min = query_agric_column(pkFinca,'t2m_min') 
            # response_t2mdew = query_agric_column(pkFinca,'t2mdew') 
            response_prect = query_agric_column(pkFinca,'prectotcorr') 
            # response_rh2m = query_agric_column(pkFinca,'rh2m')         
            # response_ws2m = query_agric_column(pkFinca,'ws2m')   

            if (response_prect['response'] == 'OK'):
            # if (response_allsky.response'] == 'OK' or 
            #     response_clrsky.response'] == 'OK' or
            #     response_t2m_max.response'] == 'OK' or
            #     response_t2m_min.response'] == 'OK' or
            #     response_t2mdew.response'] == 'OK' or
            #     response_prect.response'] == 'OK' or
            #     response_rh2m.response'] == 'OK' or
            #     response_ws2m.response'] == 'OK'):

                try:
                    result = main(
                                    pkFinca,
                                    json.loads(response_prect['data_forecasts']),
                                    ast.literal_eval(response_prect['final_columns']),
                                    ast.literal_eval(response_prect['final_probs']),
                                    'agricultural engineer'
                                )
                except Exception as e:
                    context = {'status': 'ERROR', 'message': 'Ocurrio un error al ejecutar el modelo de optimización: {}'.format(e), 'type': 'create'}
                    return JsonResponse(context)
                

                nuevo_modelo = TwoStageFincaModel(
                    finca=finca,
                    Irrigation_and_drainage=json.dumps(result)
                )
                
                nuevo_modelo.save()
            
                context = {'status': 'success', 'message': 'ok', 'type': 'create'}
                return JsonResponse(context)
            else:
                context = {'status': 'ERROR', 'message': 'Falta una columna dentro del modelo, por favor revisar que todas esten pronosticadas.', 'type': 'create'}
                return JsonResponse(context)


        else:
            context = {'status': 'error', 'message': 'Solicitud no valida.', 'type': 'create'}
            return JsonResponse(context)
    else:
        context['state'] = "error"
        context['message'] = "No tienes permiso para acceder a esta información."
        return JsonResponse(context, status=400)


class TwoStageFincaModelDeleteView(DeleteView):
    model = TwoStageFincaModel
    success_url = 'agricultural_engineer/data_clim_finca_list.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        id = self.object.id
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            try:
                obj = TwoStageFincaModel.objects.get(id=id)
            except TwoStageFincaModel.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Id de drenado e irragación no no encontrado.', 'type':'delete'})
            
            try:
                response = self.delete(request, *args, **kwargs)
                if response.status_code == 302: 
                    return JsonResponse({'status': 'success', 'message': 'Los datos de drenado e irragación, se eliminaron correctamente.', 'type':'delete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se pudo eliminar los datos de drenado e irragación.', 'type':'delete'})
            except ProtectedError:
                return JsonResponse({'status': 'error', 'message': 'No se puede eliminar los datos de drenado e irragación porque existen registros asociados en otras tablas.', 'type':'delete'})

        else:
            return JsonResponse({'status': 'error', 'message': 'La solicitud no es AJAX', 'type':'delete'})


#End script TwoStageFincaModel
#-----------------------------------------------------------------------------------------------------------------------------


    
