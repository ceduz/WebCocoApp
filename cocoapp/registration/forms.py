from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserCreationFormWithEmail(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Requerido. 254 caracteres como máximo y debe ser válido")
    first_name = forms.TextInput()
    last_name = forms.TextInput()

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("El email ya esta registrado, pruebe con otro.")        
        return email