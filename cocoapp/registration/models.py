from django.db import models
from django.contrib.auth.models import User

def custom_upload_to(instance, filename):
    old_instance = PersonalInformation.objects.get(pk=instance.pk)
    old_instance.avatar.delete()
    return 'personal_information/' + filename

# Create your models here

class Profile(models.Model):
    profile = models.CharField(max_length=50, verbose_name="Nombre perfil")
    descrip = models.CharField(max_length=250, verbose_name="Descripción de perfil")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
        ordering = ['-created']

    def __str__(self):
        return self.profile

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="Perfil asignado")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfil de usuarios"
        ordering = ['-created']

    def __str__(self):
        return self.user.username
    
class PersonalInformation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=custom_upload_to, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)