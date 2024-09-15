#import's finca
from django.views.generic import ListView, UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import *
from .models import *
from django.contrib import messages

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
#from django.shortcuts import render, HttpResponse
from django.views.generic.base import TemplateView
from django.http import JsonResponse, Http404, HttpResponseRedirect, HttpResponse
import requests
import datetime
import locale


# Create your views here.
def farmer_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                if request.user.userprofile.profile.profile == "Agricultor":
                    pass
            except:
                raise Http404("No existe perfil asociado al usuario. Comuníquese con el administrador del sistema.")

            
            if request.user.userprofile.profile.profile == "Agricultor":
                return view_func(request, *args, **kwargs)
            else:
                raise Http404("Usuario no tiene permisos suficientes.")               
            
        else:
            raise Http404("Usuario no autenticado.")
    return _wrapped_view

class HomePageView(TemplateView):
    template_name = "farmer/weather_forecast.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj_finca = Finca.objects.filter(owner_name=self.request.user).first()


        if obj_finca:
            context['pk_finca'] = obj_finca.owner_name.id
        else:
            context['pk_finca'] = None

        return context

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

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
#-----------------------------------------------------------------------------------------------------------------------------
#Start script Mifinca
class MiFincaListView(LoginRequiredMixin, ListView):
    model = Finca
    template_name = 'finca_list.html'
    context_object_name = 'finca'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        data_finca = Finca.objects.filter(owner_name=self.request.user)

        if data_finca:
            initial_data = {}
            for df in data_finca:
                initial_data = {'name' : df.name,
                                'size_fina' : df.size_fina,
                                'latitud' : df.latitud,
                                'longitud' : df.longitud,
                                'num_trees_grown' : df.num_trees_grown,
                                'age_trees' : df.age_trees,
                                }
            
            context['form'] = FincaForm(initial=initial_data)
        else:
            context['form'] = FincaForm()
        return context

    def get_queryset(self):
        return Finca.objects.filter(owner_name=self.request.user)
    
    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
class MiFincaUpdateView(LoginRequiredMixin, UpdateView):
    model = Finca
    form_class = FincaForm
    #template_name = 'finca_update.html'
    success_url = reverse_lazy('myFinca')

    def form_valid(self, form):
        instance = form.save(commit=False)
        # Obtenemos los datos originales del objeto desde la base de datos
        original_instance = self.get_object()
        field_dist = []

        # Comparamos los campos de las instancias uno por uno
        for field in instance._meta.fields:
            if getattr(instance, field.attname) != getattr(original_instance, field.attname):
                field_dist.append(field.verbose_name)  # Agregar el nombre del campo a la lista si es diferente

        if not field_dist:
            # Si los datos son iguales, mostramos un mensaje de error
            messages.warning(self.request, "Los datos son iguales, no se ha realizado ninguna modificación.")
            return HttpResponseRedirect(self.get_success_url())
        
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class MiFincaCreateView(LoginRequiredMixin, CreateView):
    form_class = FincaForm
    success_url = reverse_lazy('myFinca')
    #template_name = 'finca_create.html'

    def form_valid(self, form):
        form.instance.owner_name = self.request.user
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
#End script Mifinca
#-----------------------------------------------------------------------------------------------------------------------------
#Start script CultivationNovelty
class CultivationNoveltyListView(LoginRequiredMixin, ListView):
    model = CultivationNovelty
    template_name = 'cultivationNovelty_list.html'
    context_object_name = 'cultivation_novelty'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        finca_instance = None
        try:
            finca_instance = Finca.objects.get(owner_name=self.request.user)
            context['finca_instance'] = finca_instance
        except Finca.DoesNotExist:
            context['finca_instance'] = finca_instance

        cultivation_novelties = context['cultivation_novelty'] #busca el contexto el nombre de la variable para cambiarla antes de enviarla

        for novelty in cultivation_novelties:
            novelty.pruning = "Sí" if novelty.pruning else "No"
            novelty.pest_control = "Sí" if novelty.pest_control else "No"
        context['form'] = CultivationNoveltyForm()
        return context

    def get_queryset(self):
        try:
            finca_instance = Finca.objects.get(owner_name=self.request.user)
            return CultivationNovelty.objects.filter(finca=finca_instance)
        except Finca.DoesNotExist:
            return CultivationNovelty.objects.none()

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class CultNovUpdateView(LoginRequiredMixin, UpdateView):
    model = CultivationNovelty
    form_class = CultivationNoveltyForm
    template_name = 'farmer/cultivationNovelty_form.html'
    #success_url = reverse_lazy('cultivationNovelty')
   
    def get_success_url(self):
        return reverse_lazy('cultNov-update', args=[self.object.id])

    def get_object(self, queryset=None):
        return get_object_or_404(CultivationNovelty, id=self.kwargs['pk'])
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        # se obtienen los datos originales del objeto desde la base de datos
        original_instance = self.get_object()
        field_dist = []

        # Comparamos los campos de las instancias uno por uno
        for field in instance._meta.fields:
            if getattr(instance, field.attname) != getattr(original_instance, field.attname):
                field_dist.append(field.verbose_name)  # Agregar el nombre del campo a la lista si es diferente

        if not field_dist:
            # Si los datos son iguales, mostramos un mensaje de error
            messages.warning(self.request, "Los datos son iguales, no se ha realizado ninguna modificación.")
            return HttpResponseRedirect(self.get_success_url())
        

        # Valida el objeto Inventory
        try:
            #validación si se recibe abono
            fertilizer_old = original_instance.fertilizer
            fertilizer_current = instance.fertilizer
            pkInventory = instance.inventory.pk
            if pkInventory:
                inventary = Inventory.objects.get(pk=pkInventory)
                inventory_stock = inventary.quantity_stock

                result_stock = inventory_stock - (fertilizer_current - fertilizer_old)
                if result_stock < 0:
                    form.add_error('fertilizer', 'No tienen suficiente producto en stock.')
                    return self.form_invalid(form)
                else:
                    inventory_instance, created = Inventory.objects.get_or_create(pk=pkInventory) 
                    inventory_instance.quantity_stock -= (fertilizer_current - fertilizer_old)
                    inventory_instance.quantity_consumed += (fertilizer_current - fertilizer_old)
                    inventory_instance.save()
                
        except Inventory.DoesNotExist:
            form.add_error('fertilizer', 'No existe un abono en el inventario.')
            return self.form_invalid(form)
        except AttributeError:
            form.add_error('inventory', 'No existe un producto abono en el inventario.')
            form.add_error('fertilizer', 'Debe seleccionar un producto de abono.')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, "Ocurrio un error en el aplicativo: {}".format(e))
            return HttpResponseRedirect(self.get_success_url())
        
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class CultNovCreateView(LoginRequiredMixin, CreateView):
    form_class = CultivationNoveltyForm
    template_name = 'farmer/cultivationNovelty_add.html'
    #success_url = reverse_lazy('cultivationNovelty')

    def get_success_url(self):
        return reverse_lazy('cultNov-create')

    def form_valid(self, form):
        instance = form.save(commit=False)
        #validación si se recibe abono
        if instance.fertilizer > 0: 
            fertilizer = instance.fertilizer
            # Valida el objeto Inventory
            try:
                pkInventory = instance.inventory.pk
                if pkInventory:
                    inventary = Inventory.objects.get(pk=pkInventory)
                    inventory_stock = inventary.quantity_stock

                    result_stock = inventory_stock - fertilizer
                    if result_stock < 0:
                        form.add_error('fertilizer', 'No tienen suficiente producto en stock.')
                        return self.form_invalid(form)
                    else:
                        inventory_instance, created = Inventory.objects.get_or_create(pk=pkInventory) 
                        inventory_instance.quantity_stock -= fertilizer
                        inventory_instance.quantity_consumed += fertilizer
                        inventory_instance.save()
            except Inventory.DoesNotExist:
                form.add_error('fertilizer', 'No existe un abono en el inventario.')
                return self.form_invalid(form)
            except AttributeError:
                form.add_error('inventory', 'No existe un producto abono en el inventario.')
                form.add_error('fertilizer', 'Debe seleccionar un producto de abono.')
                return self.form_invalid(form)
            except Exception as e:
                messages.error(self.request, "Ocurrio un error en el aplicativo: {}".format(e))
                return HttpResponseRedirect(self.get_success_url())


        instance.finca = Finca.objects.get(owner_name=self.request.user)        
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
#End script CultivationNovelty
#-----------------------------------------------------------------------------------------------------------------------------
#Start script Inventory
class InventoryListView(LoginRequiredMixin, ListView):
    model = Inventory
    template_name = 'inventory_list.html'
    context_object_name = 'inventory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        finca_instance = None
        try:
            finca_instance = Finca.objects.get(owner_name=self.request.user)
            context['finca_instance'] = finca_instance
        except Finca.DoesNotExist:
            context['finca_instance'] = finca_instance

        return context

    def get_queryset(self):
        try:
            finca_instance = Finca.objects.get(owner_name=self.request.user)
            return Inventory.objects.filter(finca=finca_instance)
        except Finca.DoesNotExist:
            return Inventory.objects.none()

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class InventoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Inventory
    form_class = InventoryUpdForm
    #success_url = reverse_lazy('inventory')
    template_name = 'farmer/inventory_form.html'
    #template_name = 'farmer/cultivation_novelty_update.html'

    def get_success_url(self):
        return reverse_lazy('inventory-update', args=[self.object.id])

    def get_object(self, queryset=None):
        return get_object_or_404(Inventory, id=self.kwargs['pk'])

    def form_valid(self, form):
        instance = form.save(commit=False)
        # Obtenemos los datos originales del objeto desde la base de datos
        original_instance = self.get_object()
        field_dist = []

        # Comparamos los campos de las instancias uno por uno
        for field in instance._meta.fields:
            if getattr(instance, field.attname) != getattr(original_instance, field.attname):
                field_dist.append(field.verbose_name)  # Agregar el nombre del campo a la lista si es diferente

        if not field_dist:
            # Si los datos son iguales, mostramos un mensaje de error
            messages.warning(self.request, "Los datos son iguales, no se ha realizado ninguna modificación.")
            return HttpResponseRedirect(self.get_success_url())
        
        #validación para los productos en stock
        purchased_amount = form.cleaned_data['purchased_amount']
        quantity_consumed = form.cleaned_data['quantity_consumed']

        # Verificar que cantidad_consumido no sea mayor que cantidad_comprado
        if quantity_consumed > purchased_amount:
            form.fields['quantity_consumed'].widget.attrs['class'] += ' is-invalid'
            form.add_error('quantity_consumed', 'La cantidad consumida no puede ser mayor que la cantidad comprada.')
            return self.form_invalid(form)

        # Calcular el nuevo valor de stock
        new_stock = purchased_amount - quantity_consumed

        # Asignar el nuevo valor de stock al objeto actual
        instance.quantity_stock = new_stock
        
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

class InventoryCreateView(LoginRequiredMixin, CreateView):
    form_class = InventoryAddForm
    #success_url = reverse_lazy('inventory')
    template_name = 'farmer/inventory_add.html'

    def get_success_url(self):
        return reverse_lazy('inventory-create')

    def form_valid(self, form):
        form.instance.finca = Finca.objects.get(owner_name=self.request.user)        
        messages.success(self.request, 'Cambios guardados exitosamente.')
        return super().form_valid(form)

    @method_decorator(farmer_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
#End script Inventory
#-----------------------------------------------------------------------------------------------------------------------------
