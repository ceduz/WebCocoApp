from django.urls import path
from . import views

urlpatterns = [
    path('', views.contact_public, name="contact"),
    path('private/', views.contact_private, name="contact_private")
]