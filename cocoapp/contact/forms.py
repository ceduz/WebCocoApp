from django import forms
from django_recaptcha.fields import ReCaptchaField

class ContactPublicForm(forms.Form):
    MESSAGE_CHOICES = [
        ('', 'Seleccione un tipo de mensaje'),
        ('creacion_usuario', 'Creación de usuario'),
        ('peticion', 'Petición'),
    ]
    
    ROLE_CHOICES = [
        ('', 'Seleccione un rol'),
        ('AGRICULTOR', 'Agricultor'),
        ('ING_AGRO', 'Ingeniero agrónomo'),
        ('INVE', 'Investigador'),
    ]

    name = forms.CharField(label = "Nombre", required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Escriba su nombre'}))
    email = forms.EmailField(label= "Email", required=True, widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder':'Escriba su email'}))
    type_menssage = forms.ChoiceField(choices=MESSAGE_CHOICES, label="Tipo de Mensaje", required=True, widget=forms.Select(attrs={'class':'form-control'}))
    rol = forms.ChoiceField(choices=ROLE_CHOICES, label="Rol Deseado", required=False, widget=forms.Select(attrs={'class':'form-control'}))
    menssage = forms.CharField(label="Mensaje", required=True, widget=forms.Textarea(attrs={'class':'form-control', 'rows':3, 'placeholder':'Escriba el mensaje a enviar'}))
    captcha = ReCaptchaField()


class ContactPrivateForm(forms.Form):
    MESSAGE_CHOICES = [
        ('', 'Seleccione un tipo de mensaje'),
        ('creacion_usuario', 'Creación de usuario'),
        ('peticion', 'Petición'),
        ('product', 'Registro de nuevos productos'),
    ]
    
    ROLE_CHOICES = [
        ('', 'Seleccione un rol'),
        ('AGRICULTOR', 'Agricultor'),
        ('ING_AGRO', 'Ingeniero agrónomo'),
        ('INVE', 'Investigador'),
    ]

    name = forms.CharField(label = "Nombre", required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Escriba su nombre'}))
    email = forms.EmailField(label= "Email", required=True, widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder':'Escriba su email'}))
    type_menssage = forms.ChoiceField(choices=MESSAGE_CHOICES, label="Tipo de Mensaje", required=True, widget=forms.Select(attrs={'class':'form-control'}))
    rol = forms.ChoiceField(choices=ROLE_CHOICES, label="Rol Deseado", required=False, widget=forms.Select(attrs={'class':'form-control'}))
    menssage = forms.CharField(label="Mensaje", required=True, widget=forms.Textarea(attrs={'class':'form-control', 'rows':3, 'placeholder':'Escriba el mensaje a enviar'}))
    captcha = ReCaptchaField()