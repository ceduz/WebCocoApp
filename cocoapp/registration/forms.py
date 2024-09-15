from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import PersonalInformation
from django.core.exceptions import ValidationError

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
    

class PersonalInformationForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control mt-3', 'placeholder': 'Nombre'})
    )
    last_name = forms.CharField(
        label="Apellido",
        widget=forms.TextInput(attrs={'class': 'form-control mt-3', 'placeholder': 'Apellido'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control mt-3', 'placeholder': 'Email'})
    )

    class Meta:
        model = PersonalInformation
        fields = ['avatar', 'bio', 'first_name', 'last_name', 'email']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class':'form-control-file mt-3'}),
            'bio': forms.Textarea(attrs={'class':'form-control mt-3', 'rows':3, 'placeholder':'Biografía'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PersonalInformationForm, self).__init__(*args, **kwargs)
        if user:
            self.user = user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Este email ya está en uso. Por favor, elige otro.')
        return email

    def save(self, commit=True):
        personal_information = super(PersonalInformationForm, self).save(commit=False)
        user = personal_information.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            personal_information.save()
        return personal_information