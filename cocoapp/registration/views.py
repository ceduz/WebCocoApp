from django.contrib import messages
from .forms import UserCreationFormWithEmail, PersonalInformationForm
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .models import PersonalInformation, UserProfile
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required 
from django.shortcuts import redirect
from django.http import Http404
from django import forms   

def redirect_login(request):
    return redirect('login')

def redirect_based_on_profile(request):
    user = request.user
    if user.userprofile.profile.profile == "Agricultor":
        return redirect('index_farmer')
    elif user.userprofile.profile.profile == "Investigador":
        return redirect('apiParametersFinca')
    elif user.userprofile.profile.profile == "Ingeniero Agrónomo":
        return redirect('aPIParameterNasaFinca')
    else:
        raise Http404("Perfil no existe.")


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


@method_decorator(login_required, name='dispatch')
class PersonalInformationUpdate(UpdateView):
    form_class = PersonalInformationForm
    success_url = reverse_lazy('personal_information')
    template_name = 'registration/personal_information_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_object(self):
        persInfor, create = PersonalInformation.objects.get_or_create(user=self.request.user)
        return persInfor
    
    def form_valid(self, form):
        messages.success(self.request, "Los cambios se han guardado exitosamente.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = UserProfile.objects.get(user=self.request.user)
        context['user_profile'] = user_profile
        return context