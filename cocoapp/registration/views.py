from .forms import UserCreationFormWithEmail
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.http import Http404
from django import forms   

def redirect_login(request):
    return redirect('login')

def redirect_based_on_profile(request):
    user = request.user
    if user.userprofile.profile.profile == "Agricultor":
        return redirect('index_farmer')
    elif user.userprofile.profile.profile == "Ingeniero Agronomo":
        return redirect('index_farmer')
    else:
        raise Http404("Usuario no autenticado.")


# Create your views here.
class SignUpView(CreateView):
    form_class = UserCreationFormWithEmail
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def get_success_url(self):
        return reverse_lazy('login') + '?register'
    
    def get_form(self, form_class = None):
        form = super(SignUpView, self).get_form()
        form.fields['username'].widget = forms.TextInput(attrs={'class':'form-control', 'placeholder':'Usuario'})
        form.fields['email'].widget = forms.EmailInput(attrs={'class':'form-control', 'placeholder':'Dirección Email'})
        form.fields['first_name'].widget = forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombre', 'required': True})
        form.fields['last_name'].widget = forms.TextInput(attrs={'class':'form-control', 'placeholder':'Apellidos',  'required': True})
        form.fields['password1'].widget = forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'Contraseña'})
        form.fields['password2'].widget = forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'Repita la contraseña'})

        form.fields['username'].label = ''
        form.fields['email'].label = ''
        form.fields['first_name'].label = ''
        form.fields['last_name'].label = ''
        form.fields['password1'].label = ''
        form.fields['password2'].label = ''
        return form