from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import EmailMessage
from .forms import ContactPublicForm, ContactPrivateForm
from django.contrib import messages

# Create your views here.
def contact_public(request):
    if request.method == 'POST':
        form = ContactPublicForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            type_menssage = form.cleaned_data['type_menssage']
            rol = form.cleaned_data['rol']
            menssage = form.cleaned_data['menssage']
            types_messages = {'creacion_usuario':'Creación de usuario', 'peticion':'Petición'}
            desc_type_message = types_messages[type_menssage]
            desc_rol=''
            inf_rol = ''

            if type_menssage == 'creacion_usuario':
                rols = {'AGRICULTOR':'Agricultor',
                        'ING_AGRO':'Ingeniero agrónomo',
                        'INVE':'Investigador'}
                desc_rol = rols[rol]
                inf_rol = "\n\nRol solicitado:"+desc_rol+""

            text_send = "De {}, Email:<{}>\nAsunto:{}{}\n\nEscribió:\n{}".format(name, email, desc_type_message, inf_rol, menssage)
            
            email = EmailMessage(
                "COCOAPP: Nuevo mensaje de contacto publico",
                text_send,
                "no-contestar@inbox.cocoapp.io",
                ["ltalero@admin.co"],
                reply_to=[email]
            )
            try:
                email.send()
                messages.success(request, "Su mensaje se ha enviado correctamente, nos pondremos en contacto vía email tan pronto como sea posible.")
            except:
                messages.error(request, "Algo no ha ido bien. Por favor, inténtalo más tarde. Si el error persiste, comuníquese al correo: ltalero@admin.co")
                
            return redirect(reverse('contact'))

    else:
        form = ContactPublicForm()

    return render(request, "contact/contact.html", {'form': form})


def contact_private(request):
    if request.method == 'POST':
        form = ContactPrivateForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            type_menssage = form.cleaned_data['type_menssage']
            rol = form.cleaned_data['rol']
            menssage = form.cleaned_data['menssage']
            types_messages = {'creacion_usuario':'Creación de usuario', 'peticion':'Petición', 'product':'Registro de nuevos productos'}
            desc_type_message = types_messages[type_menssage]
            desc_rol=''
            inf_rol = ''

            if type_menssage == 'creacion_usuario':
                rols = {'AGRICULTOR':'Agricultor',
                        'ING_AGRO':'Ingeniero agrónomo',
                        'INVE':'Investigador'}
                desc_rol = rols[rol]
                inf_rol = "\n\nRol solicitado:"+desc_rol+""

            text_send = "De {}, Email:<{}>\nAsunto:{}{}\n\nEscribió:\n{}".format(name, email, desc_type_message, inf_rol, menssage)
            
            email = EmailMessage(
                "COCOAPP: Nuevo mensaje de contacto publico",
                text_send,
                "no-contestar@inbox.cocoapp.io",
                ["ltalero@admin.co"],
                reply_to=[email]
            )
            try:
                email.send()
                messages.success(request, "Su mensaje se ha enviado correctamente, nos pondremos en contacto vía email tan pronto como sea posible.")
            except:
                messages.error(request, "Algo no ha ido bien. Por favor, inténtalo más tarde. Si el error persiste, comuníquese al correo: ltalero@admin.co")
                
            return redirect(reverse('contact_private'))

    else:
        form = ContactPrivateForm()

    return render(request, "contact/contact_private.html", {'form': form})