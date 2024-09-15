from django import forms
from .models import *
from django.utils.safestring import SafeString

class APIParameterNasaFincaForm(forms.ModelForm):
    def as_div(self):
        """Add CSS Styling to divs"""
        return SafeString(super().as_div().replace("<div>", "<div class='form-group'>"))
    
    class Meta:
        model = APIParameterNasaFinca
        fields = ['finca',]
        widgets = {
            'finca': forms.Select(attrs={'class':'form-control'}),
        }
    
