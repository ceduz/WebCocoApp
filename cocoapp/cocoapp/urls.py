"""
URL configuration for cocoapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from .views import redirect_login

urlpatterns = [
    #proyect
    path('', redirect_login, name='redirect_login'),
    # Paths del farmer
    path('farmer/', include('farmer.urls')),
    # Paths del researcher
    path('researcher/', include('researcher.urls')),
    # Paths del agricultural_engineer
    path('agricultural/', include('agricultural_engineer.urls')),
    # Paths del admin
    path('admin/', admin.site.urls),
    # Paths de auth
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('registration.urls')),
    #contact
    path('contact/', include('contact.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root =settings.MEDIA_ROOT )
