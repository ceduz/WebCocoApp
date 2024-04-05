from django.contrib import admin
from .models import Profile, UserProfile

# Register your models here.
class ProfileServiceAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'updated')

class UserProfileServiceAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'updated')
    list_display = ('user', 'profile', )

admin.site.register(Profile, ProfileServiceAdmin)
admin.site.register(UserProfile, UserProfileServiceAdmin)