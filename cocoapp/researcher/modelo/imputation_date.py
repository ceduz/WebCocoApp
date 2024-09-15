
import pandas as pd
from ..models import DataApiNasa
from agricultural_engineer.models import DataApiNasaFinca
from sklearn.impute import KNNImputer
import numpy as np

"""
from investigator.modelo.imputation_date import imputation
imputation(1, 
            "prueba", 
            "PROM-HIST",
            "KNN",
            "KNN",
            "KNN",
            "KNN",
            "KNN",
            "KNN",
            "KNN") 
"""
def set_imputation_column(df, data):
    df_dummy = df.copy()
    for column, value in data.items():

        if (value == 'PROM-HIST'):
            
            year_negative = df_dummy[df_dummy[column] == -999.00]['date'].dt.year.unique()
            count = 0

            for i in sorted(year_negative):
                df_years = df_dummy[df_dummy['date'].dt.year < i-count].copy()
                df_years.loc[:, 'month_day'] = df_years['date'].dt.strftime('%m-%d')
                df_pivots = df_years.pivot_table(index='month_day', columns=df_years['date'].dt.year, values=column, aggfunc='first')

                df_year_errors = df_dummy[df_dummy['date'].dt.year == i].copy()
                df_year_errors.loc[:, 'month_day'] = df_year_errors['date'].dt.strftime('%m-%d')
                df_pivot_err = df_year_errors.pivot_table(index='month_day', columns=df_year_errors['date'].dt.year, values=column, aggfunc='first')

                values_negative = df_pivot_err[df_pivot_err.eq(-999.0)].stack()

                for idx, val in values_negative.items():
                    complete_date = f'{i}-{idx[0]}'
                    mean_years = df_pivots.loc[idx[0]].mean()
                    df_pivot_err.at[idx[0], 'new_values'] = mean_years.round(2)
                    df_pivot_err.at[idx[0], 'complete_date'] = complete_date

                for index, row in df.iterrows():
                    date_to_find = row['date'].strftime('%Y-%m-%d')
                    row_year_err = df_pivot_err[df_pivot_err['complete_date'] == date_to_find]

                    if not row_year_err.empty:
                        # Actualizar los valores en el primer DataFrame con los valores del segundo DataFrame
                        df.at[index, column] = row_year_err.values[0][1]

                count+=1
        elif (value == 'KNN'):
            #df[column].replace(-999.0, np.nan, inplace=True)
            df.replace({column: {-999.0: np.nan}}, inplace=True)
            # Instancia el imputador KNN
            imputer = KNNImputer(n_neighbors=5)  # Elige el número de vecinos a considerar

            # Transforma la columna 'temperaturas' usando el imputador KNN
            columna_interp = df[[column]]  # Selecciona la columna que quieres interpolar
            df[column] = imputer.fit_transform(columna_interp) #se redondea a 2 decimales
            df[column] = df[column].round(2)


    return df

def imputation(perfil, pk, name_finca, allsky_sfc_sw_dwn, clrsky_sfc_sw_dwn, t2m_max, t2m_min, t2mdew, prectotcorr, rh2m, ws2m): 
    data = {'allsky_sfc_sw_dwn': allsky_sfc_sw_dwn,
            'clrsky_sfc_sw_dwn': clrsky_sfc_sw_dwn,
            't2m_max': t2m_max,
            't2m_min': t2m_min,
            't2mdew': t2mdew,
            'prectotcorr': prectotcorr,
            'rh2m': rh2m,
            'ws2m': ws2m}
    if perfil == 'researcher':
        obj_clim = DataApiNasa.objects.filter(api_parameters_finca_id=pk)
    else:
        obj_clim = DataApiNasaFinca.objects.filter(api_parameters_finca_id=pk)
    
    if not obj_clim.exists():
        raise ValueError("No existen valores climaticos guardados para la finca {}".format(name_finca))
    
    datos_dict = list(obj_clim.values())
    name_columns = ['id', 'api_parameters_finca_id', 'date', 'allsky_sfc_sw_dwn', 'clrsky_sfc_sw_dwn', 't2m_max', 't2m_min', 't2mdew', 'prectotcorr', 'rh2m', 'ws2m']
    df = pd.DataFrame(datos_dict, columns=name_columns)
    drop_columns = ['id', 'api_parameters_finca_id']
    df = df.drop(columns=drop_columns)

    df['date'] = pd.to_datetime(df['date'])

    df_result = set_imputation_column(df, data)

    return df_result
