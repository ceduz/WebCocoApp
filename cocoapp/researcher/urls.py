from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('climatological/', login_required(ApiParametersFincaListView.as_view()), name="apiParametersFinca"),
    path('climatological/create/', login_required(ApiParametersFincaCreateView.as_view()), name='climatological-create'),
    path('climatological/delete/<int:pk>/', login_required(ApiParametersFincaDeleteView.as_view()), name='climatological-delete'),
    path('climatological/<int:id_filtrado>/', login_required(DataNasaListView.as_view()), name='dNasa'),
    path('climatological/update/', login_required(update_data_nasa), name='update_data_nasa'),
    #TypeImpFieldDataClima
    path('imputation/', login_required(TypeImpFieldDataClimaListView.as_view()), name="typeImpFieldDataClima"),
    path('imputation/create/', login_required(TypeImpFieldDataClimaCreateView.as_view()), name='typeImpFieldDataClima-create'),
    path('imputation/<int:pk>/update/', login_required(TypeImpFieldDataClimaUpdateView.as_view()), name='typeImpFieldDataClima-update'),
    path('imputation/delete/<int:pk>/', login_required(TypeImpFieldDataClimaDeleteView.as_view()), name='typeImpFieldDataClima-delete'),
    path('imputation/dataImput/', login_required(get_data_imput_chart), name='dataImput'),
    path('imputation/dataImputColumn/', login_required(get_dtColumn_imput), name='dataImputColumn'),
    path('imputation/dataColumnImputation/', login_required(get_column_dataNasa), name='dataColumnImputation'),
    path('imputation/updateChart/', login_required(get_data_rangeImput), name='updateChart'),
    #ModelDeterministic
    path('model/deterministicModel/', login_required(ParamDeterministicModelListView.as_view()), name="paramDeterministicModel"),
    path('model/deterministicModel/create/', login_required(ParamDeterministicModelCreateView.as_view()), name='paramDeterministicModel-create'),
    path('model/deterministicModel/<int:id_filtrado>/', login_required(DeterministicListView.as_view()), name='dDeterministic'),
    path('model/deterministicModel/delete/<int:pk>/', login_required(ParamDeterministicModelDeleteView.as_view()), name='paramDeterministicModel-delete'),
    #IterativeModelling
    path('model/iterativeModelling/', login_required(IterativeModellingListView.as_view()), name="iterativeModelling"),
    path('model/iterativeModelling/create/', login_required(IterativeModellingCreateView.as_view()), name='iterativeModelling-create'),
    path('model/iterativeModelling/summaryModelling/', login_required(get_data_iterative_modelling), name='summaryModelling'),
    path('model/iterativeModelling/graphfModelling/', login_required(get_graph_iterative_modelling), name='graphModelling'),
    path('model/iterativeModelling/delete/<int:pk>/', login_required(IterativeModellingDeleteView.as_view()), name='iterativeModelling-delete'),
    #ForecastScenarios
    path('model/forecastScenarios/', login_required(ForecastScenariosListView.as_view()), name="forecastScenarios"),
    path('model/forecastScenarios/create/', login_required(ForecastScenariosCreateView.as_view()), name='forecastScenarios-create'),
    path('model/forecastScenarios/graphForecastScenarios/', login_required(get_graph_forecast_scenarios), name='graphForecastScenarios'),
    path('model/forecastScenarios/delete/<int:pk>/', login_required(ForecastScenariosDeleteView.as_view()), name='forecastScenarios-delete'),
    #MergeScenarios
    path('model/mergeScenarios/', login_required(MergeScenariosListView.as_view()), name="mergeScenarios"),
    path('model/mergeScenarios/create/', login_required(MergeScenariosCreateView.as_view()), name='mergeScenarios-create'),
    path('model/mergeScenarios/graphMergeScenarios/', login_required(get_graph_merge_scenarios), name='graphMergeScenarios'),
    path('model/mergeScenarios/delete/<int:pk>/', login_required(MergeScenariosDeleteView.as_view()), name='mergeScenarios-delete'),
    #TwoStageModel
    path('model/twoStageModel/', login_required(TwoStageModelListView.as_view()), name="twoStageModel"),
    path('model/twoStageModel/create/', login_required(TwoStageModelCreateView.as_view()), name='twoStageModel-create'),
    path('model/twoStageModel/delete/<int:pk>/', login_required(TwoStageModelDeleteView.as_view()), name='twoStageModel-delete'),
]