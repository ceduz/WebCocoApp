from django import forms
from .models import *
from django.utils.safestring import SafeString
from datetime import datetime


class FincaForm(forms.ModelForm):
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = Finca
        fields = ['name', 'size_fina', 'latitud', 'longitud', 'num_trees_grown', 'age_trees',]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'size_fina': forms.NumberInput(attrs={'class':'form-control'}),
            'latitud': forms.NumberInput(attrs={'class':'form-control'}),
            'longitud': forms.NumberInput(attrs={'class':'form-control'}),
            'num_trees_grown': forms.NumberInput(attrs={'class':'form-control'}),
            'age_trees': forms.NumberInput(attrs={'class':'form-control'}),
        }
    

class CultivationNoveltyForm(forms.ModelForm):
    class Meta:
        model = CultivationNovelty
        fields = ['harvest', 'irrigation', 'inventory', 'fertilizer', 'pruning', 'pest_control',]
        widgets = {
            'harvest': forms.NumberInput(attrs={'class':'form-control'}),
            'irrigation': forms.NumberInput(attrs={'class':'form-control'}),
            'inventory': forms.Select(attrs={'class':'form-control'}),
            'fertilizer': forms.NumberInput(attrs={'class':'form-control'}),
            'pruning': forms.Select(attrs={'class':'form-control'}),
            'pest_control': forms.Select(attrs={'class':'form-control'}),
        }

    pruning = forms.CharField(
        label = CultivationNovelty._meta.get_field('pruning').verbose_name,
        widget = forms.Select(choices=[('', 'Seleccione una opción'), ('True', 'Sí'), ('False', 'No')],
                            attrs={'class': 'form-control'})
    )

    pest_control = forms.CharField(
        label = CultivationNovelty._meta.get_field('pest_control').verbose_name,
        widget=forms.Select(choices=[('', 'Seleccione una opción'), ('True', 'Sí'), ('False', 'No')],
                            attrs={'class': 'form-control'})
    )

    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener el valor inicial de 'pruning' y 'pest_control'
        pruning_initial = kwargs.get('initial', {}).get('pruning')
        pest_control_initial = kwargs.get('initial', {}).get('pest_control')
        # Establecer la opción seleccionada en el widget de selección
        if pruning_initial is not None:
            self.fields['pruning'].initial = pruning_initial
        if pest_control_initial is not None:
            self.fields['pest_control'].initial = pest_control_initial
            
        self.fields['inventory'].queryset = Inventory.objects.filter(
            category__name='Abono',
            quantity_stock__gt=0
        )
        self.fields['inventory'].required = False

class CategoryProductForm(forms.ModelForm):
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = CategoryProduct
        fields = ['name', 'description', ]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.TextInput(attrs={'class':'form-control'}),
        }

class InventoryUpdForm(forms.ModelForm):    
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = Inventory
        fields = ['name', 'composition', 'category', 'due_date', 'unit_value', 'purchased_amount', 'quantity_consumed', ]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'composition': forms.Textarea(attrs={'class':'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class':'form-control'}),
            'due_date': forms.DateInput(attrs={'class':'form-control datetimepicker-input', 'data-target':'#reservationdate'}),
            'unit_value': forms.NumberInput(attrs={'class':'form-control'}),
            'purchased_amount': forms.NumberInput(attrs={'class':'form-control'}),
            'quantity_consumed': forms.NumberInput(attrs={'class':'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['composition'].required = False
        # Agregar clase al campo de due_date si hay un error de validación
        if self.errors.get('due_date'):
            self.fields['due_date'].widget.attrs['class'] += ' is-invalid'

class InventoryAddForm(forms.ModelForm):    
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = Inventory
        fields = ['name', 'composition', 'category', 'due_date', 'unit_value', 'purchased_amount',]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'composition': forms.Textarea(attrs={'class':'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class':'form-control'}),
            'due_date': forms.DateInput(attrs={'class':'form-control datetimepicker-input', 'data-target':'#reservationdate'}),
            'unit_value': forms.NumberInput(attrs={'class':'form-control'}),
            'purchased_amount': forms.NumberInput(attrs={'class':'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['composition'].required = False
        # Agregar clase al campo de due_date si hay un error de validación
        if self.errors.get('due_date'):
            self.fields['due_date'].widget.attrs['class'] += ' is-invalid'