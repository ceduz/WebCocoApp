import os
import json
import requests
import pandas as pd
from datetime import datetime

def get_api_data(latitude, longitude, start_date, end_date, variables):
    parameters = ','.join(variables)
    base_url = r"https://power.larc.nasa.gov/api/temporal/daily/point?parameters={parameters}&community=AG&longitude={longitude}&latitude={latitude}&start={start}&end={end}&format=JSON"
    api_request_url = base_url.format(parameters=parameters, longitude=longitude, latitude=latitude, start=start_date, end=end_date)
    response = requests.get(url=api_request_url, timeout=30.0)  
    content = json.loads(response.content.decode('utf-8'))  
    for keys in content['properties']['parameter'].keys():
        content['properties']['parameter'][keys] = transform_date_keys(content['properties']['parameter'][keys])
    return content['properties']['parameter'] 
    
def transform_date_keys(dictionary):
    transformed_dict = {}  
    for key, value in dictionary.items():
        transformed_key = key[:4] + '-' + key[4:6] + '-' + key[6:]  
        transformed_dict[transformed_key] = value  
    return transformed_dict  

def get_data(start_date, end_date, latitude, longitude):
    variables = ["ALLSKY_SFC_SW_DWN","CLRSKY_SFC_SW_DWN","T2M_MAX","T2M_MIN","T2MDEW","PRECTOTCORR","RH2M","WS2M"]
    start_date = start_date.strftime('%Y%m%d')
    end_date = end_date.strftime('%Y%m%d')

    dfs = []  
    parameters = get_api_data(latitude, longitude, start_date, end_date, variables)
    reshaped_data = {'date': []}
    for var in variables:
        reshaped_data[var] = []

    for date in pd.date_range(start=start_date, end=end_date, freq='D'):
        date_str = date.strftime('%Y-%m-%d')  
        if any(date_str in parameters[var] for var in variables):  
            reshaped_data['date'].append(date)
            for var in variables:
                reshaped_data[var].append(parameters[var].get(date_str, None))

    # Create a DataFrame from the reshaped data and append it to the list
    dfs.append(pd.DataFrame(reshaped_data))

    # Concatenate all dataframes in the list
    df = pd.concat(dfs, ignore_index=True)

    return df