from django.contrib import admin
from .models import * 

# Register your models here.
class ColumnsApiNasaServiceAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'updated')
    list_display = ('name', )

admin.site.register(ColumnsApiNasa, ColumnsApiNasaServiceAdmin)