from django.db import models
from farmer.models import Finca
from researcher.models import TypeImpFieldDataClima, ColumnsApiNasa

# Create your models here.
class APIParameterNasaFinca(models.Model):
    finca = models.OneToOneField(Finca, on_delete=models.PROTECT, primary_key=True, verbose_name="Selección de finca")
    latitud = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="Latitud")
    longitud = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="Longitud")
    date_exceute = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de ejecución")
    date_start = models.DateTimeField(verbose_name="Fecha de inicio para exportación de datos")
    date_end = models.DateTimeField(verbose_name="Fecha de fin para exportación de datos")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Parametros Api (climatológica)"
        verbose_name_plural = "Parametros Api (climatologica)"
        ordering = ['-created']


class DataApiNasaFinca(models.Model):
    api_parameters_finca = models.ForeignKey(APIParameterNasaFinca, on_delete=models.PROTECT, verbose_name="Parametros API de finca")
    date = models.DateField(max_length=50, verbose_name="Date en formato YYYY-MM-DD")
    allsky_sfc_sw_dwn = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="ALLSKY_SFC_SW_DWN")
    clrsky_sfc_sw_dwn = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="CLRSKY_SFC_SW_DWN")
    t2m_max = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="T2M_MAX")
    t2m_min = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="T2M_MIN")
    t2mdew = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="T2MDEW")
    prectotcorr = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="PRECTOTCORR")
    rh2m = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="RH2M")
    ws2m = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="WS2M")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    
    class Meta:
        verbose_name = "Datos climatilogicos de la finca"
        verbose_name_plural = "Datos climatilogicos de las fincas"
        ordering = ['date']


class DataApiNasaImputation(models.Model):
    api_parameters_finca = models.ForeignKey(APIParameterNasaFinca, on_delete=models.CASCADE, verbose_name="Datos de la finca")
    type_imp_data = models.ForeignKey(TypeImpFieldDataClima, on_delete=models.CASCADE, verbose_name="Tipo de imputación")
    date = models.DateField(verbose_name="Date en formato YYYY-MM-DD")
    allsky_sfc_sw_dwn = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="ALLSKY_SFC_SW_DWN")
    clrsky_sfc_sw_dwn = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="CLRSKY_SFC_SW_DWN")
    t2m_max = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="T2M_MAX")
    t2m_min = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="T2M_MIN")
    t2mdew = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="T2MDEW")
    prectotcorr = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="PRECTOTCORR")
    rh2m = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="RH2M")
    ws2m = models.DecimalField(max_digits=50, decimal_places=2, verbose_name="WS2M")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['date']


class PronosticModel(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, verbose_name="Nombre de la finca")
    columns_api_nasa = models.ForeignKey(ColumnsApiNasa, on_delete=models.PROTECT, verbose_name="Columna a analizar")

    selected_model = models.BinaryField()
    power = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="power")
    mean = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="mean")
    st_d = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="st_d")

    data_forecasts = models.TextField()

    final_columns = models.TextField()
    final_probs = models.TextField()

    Irrigation_and_drainage = models.TextField()

    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']


class BeastPronosticModel(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, verbose_name="Nombre de la finca")
    dia = models.CharField(max_length=4, verbose_name="Día")
    allsky_sfc_sw_dwn = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="ALLSKY_SFC_SW_DWN")
    clrsky_sfc_sw_dwn = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="CLRSKY_SFC_SW_DWN")
    t2m_max = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="T2M_MAX")
    t2m_min = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="T2M_MIN")
    t2mdew = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="T2MDEW")
    prectotcorr1 = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="PRECTOTCORR_1")
    prectotcorr2 = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="PRECTOTCORR_2")
    prectotcorr3 = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="PRECTOTCORR_3")
    rh2m = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="RH2M")
    ws2m = models.DecimalField(max_digits=50, null=True, decimal_places=2, verbose_name="WS2M")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']


class TwoStageFincaModel(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, verbose_name="Nombre de la finca")
    Irrigation_and_drainage = models.TextField()
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']