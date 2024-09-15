from django import forms
from .models import *
from farmer.models import Finca
from django.utils.safestring import SafeString

class ApiParametersFincaForm(forms.ModelForm):    
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = ApiParametersFinca
        fields = ['finca',]
        widgets = {
            'finca': forms.Select(attrs={'class':'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(ApiParametersFincaForm, self).__init__(*args, **kwargs)
        # Filtrar las opciones de modelo_principal que aún no existen en ModeloSecundario
        existing_modelos = ApiParametersFinca.objects.all().values_list('finca', flat=True)
        fincas_disp = self.fields['finca'].queryset = Finca.objects.exclude(pk__in=existing_modelos)

        if fincas_disp.exists():
            self.fields['finca'].queryset = fincas_disp
        else:
            del self.fields['finca']
            self.fields[''] = forms.CharField(disabled=True, 
                                              initial="No hay fincas disponibles para seleccionar. Ya has añadido todas!",
                                              widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'color: red;'}))
            

class TypeImpFieldDataClimaForm(forms.ModelForm):        
    class Meta:
        model = TypeImpFieldDataClima
        fields = ['finca', 'allsky_sfc_sw_dwn', 'clrsky_sfc_sw_dwn', 't2m_max', 't2m_min', 't2mdew', 'prectotcorr', 'rh2m', 'ws2m',]
        widgets = {
            'finca': forms.Select(attrs={'class':'form-control'}),
        }

    selectImputation = [('', 'Seleccione una opción'), ('KNN', 'K-NEIGHBOR'), ('PROM-HIST', 'Promedio Historico (ultimos 3 años)')]

    allsky_sfc_sw_dwn = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('allsky_sfc_sw_dwn').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    clrsky_sfc_sw_dwn = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('clrsky_sfc_sw_dwn').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    t2m_max = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('t2m_max').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    t2m_min = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('t2m_min').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )
    t2mdew = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('t2mdew').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    prectotcorr = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('prectotcorr').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    rh2m = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('rh2m').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    ws2m = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('ws2m').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar las opciones de modelo_principal que aún no existen en ModeloSecundario
        existing_modelos = TypeImpFieldDataClima.objects.all().values_list('finca', flat=True)
        fincas_disp = self.fields['finca'].queryset = Finca.objects.exclude(pk__in=existing_modelos)
        
        allsky_sfc_sw_dwn = kwargs.get('initial', {}).get('allsky_sfc_sw_dwn')
        clrsky_sfc_sw_dwn = kwargs.get('initial', {}).get('clrsky_sfc_sw_dwn')
        t2m_max = kwargs.get('initial', {}).get('t2m_max')
        t2m_min = kwargs.get('initial', {}).get('t2m_min')
        t2mdew = kwargs.get('initial', {}).get('t2mdew')
        prectotcorr = kwargs.get('initial', {}).get('prectotcorr')
        rh2m = kwargs.get('initial', {}).get('rh2m')
        ws2m = kwargs.get('initial', {}).get('ws2m')
        # Establecer la opción seleccionada en el widget de selección
        if allsky_sfc_sw_dwn is not None:
            self.fields['allsky_sfc_sw_dwn'].initial = allsky_sfc_sw_dwn
        if clrsky_sfc_sw_dwn is not None:
            self.fields['clrsky_sfc_sw_dwn'].initial = clrsky_sfc_sw_dwn
        if t2m_max is not None:
            self.fields['t2m_max'].initial = t2m_max
        if t2m_min is not None:
            self.fields['t2m_min'].initial = t2m_min
        if t2mdew is not None:
            self.fields['t2mdew'].initial = t2mdew
        if prectotcorr is not None:
            self.fields['prectotcorr'].initial = prectotcorr
        if rh2m is not None:
            self.fields['rh2m'].initial = rh2m
        if ws2m is not None:
            self.fields['ws2m'].initial = ws2m

class TypeImpFieldDataClimaFormUpd(forms.ModelForm):        
    class Meta:
        model = TypeImpFieldDataClima
        fields = ['allsky_sfc_sw_dwn', 'clrsky_sfc_sw_dwn', 't2m_max', 't2m_min', 't2mdew', 'prectotcorr', 'rh2m', 'ws2m',]

    selectImputation = [('', 'Seleccione una opción'), ('KNN', 'K-NEIGHBOR'), ('PROM-HIST', 'Promedio Historico (ultimos 3 años)')]

    allsky_sfc_sw_dwn = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('allsky_sfc_sw_dwn').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    clrsky_sfc_sw_dwn = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('clrsky_sfc_sw_dwn').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    t2m_max = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('t2m_max').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    t2m_min = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('t2m_min').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )
    t2mdew = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('t2mdew').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    prectotcorr = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('prectotcorr').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    rh2m = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('rh2m').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    ws2m = forms.CharField(
        label = TypeImpFieldDataClima._meta.get_field('ws2m').verbose_name,
        widget = forms.Select(choices=selectImputation,
                            attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        allsky_sfc_sw_dwn = kwargs.get('initial', {}).get('allsky_sfc_sw_dwn')
        clrsky_sfc_sw_dwn = kwargs.get('initial', {}).get('clrsky_sfc_sw_dwn')
        t2m_max = kwargs.get('initial', {}).get('t2m_max')
        t2m_min = kwargs.get('initial', {}).get('t2m_min')
        t2mdew = kwargs.get('initial', {}).get('t2mdew')
        prectotcorr = kwargs.get('initial', {}).get('prectotcorr')
        rh2m = kwargs.get('initial', {}).get('rh2m')
        ws2m = kwargs.get('initial', {}).get('ws2m')
        # Establecer la opción seleccionada en el widget de selección
        if allsky_sfc_sw_dwn is not None:
            self.fields['allsky_sfc_sw_dwn'].initial = allsky_sfc_sw_dwn
        if clrsky_sfc_sw_dwn is not None:
            self.fields['clrsky_sfc_sw_dwn'].initial = clrsky_sfc_sw_dwn
        if t2m_max is not None:
            self.fields['t2m_max'].initial = t2m_max
        if t2m_min is not None:
            self.fields['t2m_min'].initial = t2m_min
        if t2mdew is not None:
            self.fields['t2mdew'].initial = t2mdew
        if prectotcorr is not None:
            self.fields['prectotcorr'].initial = prectotcorr
        if rh2m is not None:
            self.fields['rh2m'].initial = rh2m
        if ws2m is not None:
            self.fields['ws2m'].initial = ws2m


class ParamDeterministicModelForm(forms.ModelForm):    
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = ParamDeterministicModel
        fields = ['finca',]
        widgets = {
            'finca': forms.Select(attrs={'class':'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(ParamDeterministicModelForm, self).__init__(*args, **kwargs)
        # Filtrar las opciones de modelo_principal que aún no existen en ModeloSecundario
        existing_modelos = ParamDeterministicModel.objects.all().values_list('finca', flat=True)
        fincas_disp = self.fields['finca'].queryset = Finca.objects.exclude(pk__in=existing_modelos)

        if fincas_disp.exists():
            self.fields['finca'].queryset = fincas_disp
        else:
            del self.fields['finca']
            self.fields[''] = forms.CharField(disabled=True, 
                                              initial="No hay fincas disponibles para seleccionar. Ya has añadido todas!",
                                              widget=forms.TextInput(attrs={'id': 'id_noFinca', 'class': 'form-control', 'style': 'color: red;'}))
            

class IterativeModellingForm(forms.ModelForm):    
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = IterativeModelling
        fields = ['finca', 'columns_api_nasa', 'max_p', 'max_q', 'max_iterations', 'n_neighbors', 'contamination',]
        widgets = {
            'finca': forms.Select(attrs={'class':'form-control'}),
            'columns_api_nasa': forms.Select(attrs={'class':'form-control'}),
            'max_p': forms.NumberInput(attrs={'class':'form-control'}),
            'max_q': forms.NumberInput(attrs={'class':'form-control'}),
            'max_iterations': forms.NumberInput(attrs={'class':'form-control'}),
            'n_neighbors': forms.NumberInput(attrs={'class':'form-control'}),
            'contamination': forms.NumberInput(attrs={'class':'form-control'}),
        }
            

class ForecastScenariosForm(forms.ModelForm):    
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = ForecastScenarios
        fields = ['cod_modelo_iter', 'steps', 'n_scenarios', 'alpha', ]
        widgets = {
            'cod_modelo_iter': forms.Select(attrs={'class':'form-control'}),
            'steps': forms.NumberInput(attrs={'class':'form-control'}),
            'n_scenarios': forms.NumberInput(attrs={'class':'form-control'}),
            'alpha': forms.NumberInput(attrs={'class':'form-control'}),
        }
     

class MergeScenariosForm(forms.ModelForm):    
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = MergeScenarios
        fields = ['cod_forecast_scen', 'q', 'tol', 'a', ]
        widgets = {
            'cod_forecast_scen': forms.Select(attrs={'class':'form-control'}),
            'q': forms.NumberInput(attrs={'class':'form-control'}),
            'tol': forms.NumberInput(attrs={'class':'form-control'}),
            'a': forms.NumberInput(attrs={'class':'form-control'}),
        }


class TwoStageModelForm(forms.ModelForm):    
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = TwoStageModel
        fields = ['finca',]
        widgets = {
            'finca': forms.Select(attrs={'class':'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(TwoStageModelForm, self).__init__(*args, **kwargs)
        # Filtrar las opciones de modelo_principal que aún no existen en ModeloSecundario
        existing_modelos = TwoStageModel.objects.all().values_list('finca', flat=True)
        fincas_disp = self.fields['finca'].queryset = Finca.objects.exclude(pk__in=existing_modelos)

        if fincas_disp.exists():
            self.fields['finca'].queryset = fincas_disp
        else:
            del self.fields['finca']
            self.fields[''] = forms.CharField(disabled=True, 
                                              initial="No hay fincas disponibles para seleccionar. Ya has añadido todas!",
                                              widget=forms.TextInput(attrs={'id': 'id_noFinca', 'class': 'form-control', 'style': 'color: red;'}))