from django.contrib import admin
from django import forms
from .models import * #Finca, CultivationNovelty, CategoryProduct, Inventory
from django.contrib.admin import AdminSite

# Register your models here.
class FincaServiceAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'updated')
    list_display = ('name', )

class CategoryProductServiceAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'updated')
    list_display = ('name', )

class InventoryAdminForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = '__all__'  # O especifica los campos que necesitas

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['composition'].required = False
        

class InventoryServiceAdmin(admin.ModelAdmin):
    form = InventoryAdminForm
    readonly_fields = ('created', 'updated')
    list_display = ('name', )

class CultivationNoveltyAdminForm(forms.ModelForm):
    class Meta:
        model = CultivationNovelty
        fields = '__all__'  # O especifica los campos que necesitas

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inventory'].queryset = Inventory.objects.filter(
            category__name='Abono',
            quantity_stock__gt=0
        )

class CultivationNoveltyServiceAdmin(admin.ModelAdmin):
    form =  CultivationNoveltyAdminForm
    readonly_fields = ('created', 'updated')
    list_display = ('id', 'finca', 'harvest', )



admin.site.register(Finca, FincaServiceAdmin)
admin.site.register(CultivationNovelty, CultivationNoveltyServiceAdmin)
admin.site.register(CategoryProduct, CategoryProductServiceAdmin)
admin.site.register(Inventory, InventoryServiceAdmin)

admin.site.site_header = "Administración del sitio"
admin.site.site_title = "Admin del sitio"
admin.site.index_title = "Bienvenido al panel de administración de COCOAPP"


