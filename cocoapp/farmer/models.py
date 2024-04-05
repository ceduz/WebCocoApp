from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Finca(models.Model):
    owner_name = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Nombre del dueño")
    name = models.CharField(max_length=250, verbose_name="Nombre de mi finca")
    size_fina = models.PositiveIntegerField(verbose_name="Tamaño de finca (m2)")
    latitud = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="Latitud")
    longitud = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="Longitud")
    num_trees_grown = models.PositiveIntegerField(verbose_name="Cantidad de árboles cultivados")
    age_trees = models.PositiveIntegerField(verbose_name="Edad de árboles (años)")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Mi finca"
        verbose_name_plural = "Mi finca"
        ordering = ['-created']

    def __str__(self):
        return str('{}'.format(self.name))

class CategoryProduct(models.Model):
    name = models.CharField(max_length=250, verbose_name="Nombre de categoria")
    description = models.CharField(max_length=500, verbose_name="Descripción de categoria")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Categoria de producto"
        verbose_name_plural = "Categorias de productos"
        ordering = ['-created']

    def __str__(self):
        return str('{}'.format(self.name))

class Inventory(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, verbose_name="Nombre de la finca")
    name = models.CharField(max_length=250, verbose_name="Nombre del producto")
    composition = models.CharField(null=True, max_length=2000, verbose_name="Descripción del producto")
    category =  models.ForeignKey(CategoryProduct, on_delete=models.CASCADE, verbose_name="Tipo de producto")
    due_date = models.DateTimeField(null=True, verbose_name="Fecha de vencimiento")
    unit_value = models.IntegerField(default=0, verbose_name="Valor unitario del producto")
    purchased_amount = models.IntegerField(default=0, verbose_name="Cantidad de producto comprado")
    quantity_consumed = models.IntegerField(default=0, verbose_name="Cantidad de producto consumido")
    quantity_stock = models.IntegerField(default=0, verbose_name="Cantidad de producto en inventario")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Inventario de producto"
        verbose_name_plural = "Inventario de productos"
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} - en inventario: {self.quantity_stock}'
    
class CultivationNovelty(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, verbose_name="Nombre de la finca")
    inventory = models.ForeignKey(Inventory, null=True, on_delete=models.CASCADE, verbose_name="Producto de abono")
    harvest = models.PositiveIntegerField(verbose_name="Cantidad de cosecha (kg)")
    irrigation = models.PositiveIntegerField(verbose_name="Cantidad de riego (mm)")
    fertilizer = models.PositiveIntegerField(verbose_name="Cantidad de abono (g)")
    pruning = models.BooleanField(verbose_name="¿Podó?")
    pest_control = models.BooleanField(verbose_name="¿Realizó control de plagas?")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Novedad de cultivo"
        verbose_name_plural = "Novedades de cultivos"
        ordering = ['-created']

    #def __str__(self):
    #    return str('{} - {} - {}'.format(self.finca.name, self.finca.owner_name, self.pk))