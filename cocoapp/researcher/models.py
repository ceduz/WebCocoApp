from django.db import models
from farmer.models import Finca
from django.core.validators import MinValueValidator

# Create your models here.
class ApiParametersFinca(models.Model):
    finca = models.OneToOneField(Finca, on_delete=models.CASCADE, primary_key=True, verbose_name="Nombre de la finca")
    latitud = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="Latitud")
    longitud = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="Longitud")
    date_exceute = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de ejecución")
    date_start = models.DateTimeField(verbose_name="Fecha de inicio para exportación de datos")
    date_end = models.DateTimeField(verbose_name="Fecha de fin para exportación de datos")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Parametros Api (climatológica)"
        verbose_name_plural = "Parametros Api (climatológica)"
        ordering = ['-created']

class DataApiNasa(models.Model):
    api_parameters_finca = models.ForeignKey(ApiParametersFinca, on_delete=models.CASCADE, verbose_name="Parametros API de finca")
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
        verbose_name_plural = "Datos climatilogicos de la fincas"
        ordering = ['date']

class TypeImpFieldDataClima(models.Model):
    finca = models.OneToOneField(Finca, on_delete=models.CASCADE, primary_key=True, verbose_name="Nombre de la finca")
    allsky_sfc_sw_dwn = models.CharField(max_length=50, verbose_name="Tipo de imputución para la columna ALLSKY_SFC_SW_DWN")
    clrsky_sfc_sw_dwn = models.CharField(max_length=50, verbose_name="Tipo de imputución para la columna CLRSKY_SFC_SW_DWN")
    t2m_max = models.CharField(max_length=50, verbose_name="Tipo de imputución para la columna T2M_MAX")
    t2m_min = models.CharField(max_length=50, verbose_name="Tipo de imputución para la columna T2M_MIN")
    t2mdew = models.CharField(max_length=50, verbose_name="Tipo de imputución para la columna T2MDEW")
    prectotcorr = models.CharField(max_length=50, verbose_name="Tipo de imputución para la columna PRECTOTCORR")
    rh2m = models.CharField(max_length=50, verbose_name="Tipo de imputución para la columna RH2M")
    ws2m = models.CharField(max_length=50, verbose_name="Tipo de imputución para la columna WS2M")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")


class DataClimImputation(models.Model):
    api_parameters_finca = models.ForeignKey(TypeImpFieldDataClima, on_delete=models.CASCADE, verbose_name="Tipo de imputación")
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


class ParamDeterministicModel(models.Model):
    finca = models.OneToOneField(Finca, on_delete=models.CASCADE, primary_key=True, verbose_name="Nombre de la finca")
    altitude = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="Altitud")


    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']

#['Time', 'ETC','Irrigation', 'Draining','Depletion', 'PAW', 'f_water', 'Heat_Stress_Surplus', 'Heat_Stress_Slack', 'Water_Excess', 'Water_Optimal', 'Objective_Value']
class DeterministicModel(models.Model):
    param_deterministic = models.ForeignKey(ParamDeterministicModel, on_delete=models.CASCADE, verbose_name="")
    time = models.PositiveIntegerField(null=True, verbose_name="Time")
    etc = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="ETC")
    irrigation = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="Irrigation")
    draining = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="Draining")
    depletion = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="Depletion")
    paw = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="PAW")
    f_water = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="f_water")
    heat_stress_surplus = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="Heat_Stress_Surplus")
    heat_stress_slack = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="Heat_Stress_Slack")
    water_excess = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="Water_Excess")
    water_optimal = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="Water_Optimal")
    objective_value = models.DecimalField(max_digits=50, null=True, decimal_places=10, verbose_name="Objective_Value")

    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']


class ColumnsApiNasa(models.Model):
    name= models.CharField(max_length=250, verbose_name="Nombre de la columna")
    description = models.CharField(max_length=500, verbose_name="Descripción")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Columna de la API-NASA"
        verbose_name_plural = "Columnas de la API-NASA"
        ordering = ['created']
    
    def __str__(self):
        return str('{}'.format(self.name))


class IterativeModelling(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, verbose_name="Nombre de la finca")
    columns_api_nasa = models.ForeignKey(ColumnsApiNasa, on_delete=models.PROTECT, verbose_name="Columna a analizar")
    
    max_p = models.IntegerField(default=25, validators=[MinValueValidator(1)], verbose_name="Max p")
    max_q = models.IntegerField(default=25, validators=[MinValueValidator(1)], verbose_name="Max q")
    max_iterations = models.IntegerField(default=20, validators=[MinValueValidator(1)], verbose_name="Cantidad de iteraciones")
    n_neighbors = models.IntegerField(default=7, validators=[MinValueValidator(1)], verbose_name="Cantidad de vecinos")
    contamination  = models.DecimalField(default=0.1, max_digits=1, decimal_places=1, validators=[MinValueValidator(0.0)], verbose_name="Contaminación")

    selected_model = models.BinaryField()
    diagnostics_image = models.BinaryField(null=True, blank=True)
    residuals_img = models.BinaryField(null=True, blank=True)
    power = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="power")
    mean = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="mean")
    st_d = models.DecimalField(max_digits=50, decimal_places=10, verbose_name="st_d")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']

    def __str__(self):
        return str('{} - {}'.format(self.pk, self.columns_api_nasa.name))


class ForecastScenarios(models.Model):
    cod_modelo_iter = models.ForeignKey(IterativeModelling, on_delete=models.CASCADE, verbose_name="Modelo iterativo")
    steps = models.IntegerField(default=0, verbose_name="Número de pasos")
    n_scenarios = models.IntegerField(default=0, verbose_name="Número de escenarios a simular")
    alpha = models.DecimalField(max_digits=20, decimal_places=5, verbose_name="Nivel de significación")
    data_forecasts = models.TextField()
    forecast_image = models.BinaryField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']

    def __str__(self):
        return str('{} - {}'.format(self.pk, self.cod_modelo_iter.columns_api_nasa.name))


class MergeScenarios(models.Model):
    cod_forecast_scen = models.ForeignKey(ForecastScenarios, on_delete=models.CASCADE, verbose_name="Código de generados de escenarios")
    q = models.IntegerField(default=0, verbose_name="Q")
    tol = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Tol")
    a = models.DecimalField(max_digits=20, decimal_places=5, verbose_name="a")
    final_columns = models.TextField()
    final_probs = models.TextField()
    merge_history = models.TextField()
    merge_image = models.BinaryField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']


class TwoStageModel(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, verbose_name="Nombre de la finca")
    Irrigation_and_drainage = models.TextField()
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        ordering = ['created']
