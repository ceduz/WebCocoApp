#import pulp
import numpy as np
import pandas as pd
import math

from sklearn.neighbors import LocalOutlierFactor
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
import itertools
import pmdarima as pm
import numpy as np
from scipy.stats import jarque_bera, norm

from .data import import_data_clim

'''
df = prueba_data()
print(df['prectotcorr'])
'''
def smooth_outliers(data, n_neighbors=20, contamination=0.3):
    """
    Smooth outliers in a pandas DataFrame using the Local Outlier Factor (LOF) method.
    Parameters:
    - data: pandas DataFrame with columns of interest.
    - n_neighbors: number of neighbors to consider for LOF.
    - contamination: proportion of outliers in the data.

    Returns:
    - pandas DataFrame with outliers smoothed.
    """
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    outliers = lof.fit_predict(data)
    data_out = data.copy()
    for col in data.columns:
        local_mean = data_out.loc[outliers == 1, col].mean()
        data_out.loc[outliers == -1, col] = local_mean
    return data_out


def test_stationarity_decompose_and_acf(series, model='additive', freq=None):
    """
    Test the stationarity of a time series, perform seasonal decomposition, and display the ADF test result with interpretation.

    Parameters:
    - series: Time series data as a pandas Series.
    - model: Type of seasonal decompose to perform, either 'additive' or 'multiplicative'.
    - freq: The frequency of the time series.

    Returns:
    - Decomposition results and ADF test result with interpretation.
    """
    # Decompose the series
    decomposition = seasonal_decompose(series, model=model, period=freq)

    # ADF Test
    print('Results of Dickey-Fuller Test:')
    dftest = adfuller(series.dropna(), autolag='AIC')
    dfoutput = pd.Series(dftest[0:4], index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
    for key, value in dftest[4].items():
        dfoutput['Critical Value (%s)' % key] = value
    print(dfoutput)

    # Hypothesis testing interpretation
    if dfoutput['p-value'] < 0.05:
        print("Reject the null hypothesis. Data does not have a unit root and is stationary.")
    else:
        print("Fail to reject the null hypothesis. Data has a unit root and is non-stationary.")

    return decomposition


def select_best_arima_auto(series, seasonal=False, m=1, max_p=25, max_q=25):
    """
    Identify the best ARIMA model using auto_arima from the pmdarima package.

    Parameters:
    - series: the time series data.
    - seasonal: Whether to consider seasonal effects.
    - m: The seasonal period, if seasonality is considered.

    Returns:
    - The best ARIMA model according to the AIC.
    """
    # Fit the auto ARIMA model
    model = pm.auto_arima(series, start_p=1, start_q=1,
                          test='adf',       # use adf test to find optimal 'd'
                          max_p=max_p, max_q=max_q, # maximum p and q
                          m=m,              # frequency of series
                          d=None,           # let model determine 'd'
                          seasonal=seasonal,   # Seasonality
                          start_P=0,
                          D=0,
                          trace=False,
                          error_action='ignore',
                          suppress_warnings=True,
                          stepwise=True)

    print("This is the best model:")
    print(model.summary())

    return model



def check_residuals_normality(residuals):
    """
    Check if the residuals of the ARIMA model are normally distributed.

    Parameters:
    - model: The fitted ARIMA model.

    Returns:
    - Jarque-Bera test result and normal distribution parameters (if applicable).
    """

    # Perform Jarque-Bera test
    jb_test_stat, jb_p_value = jarque_bera(residuals)

    print(f"Jarque-Bera test statistic: {jb_test_stat:.2f}, p-value: {jb_p_value:.2f}")

    normal_params = None
    if jb_p_value < 0.05:
        print("The residuals do not follow a normal distribution.")
    else:
        print("The residuals appear to follow a normal distribution.")
        # Fit a normal distribution to the residuals
        mu, std = norm.fit(residuals)
        normal_params = (mu, std)
        print(f"Normal distribution parameters: mean = {mu:.2f}, std = {std:.2f}")

    return normal_params


def iterative_modeling(series, max_p, max_q, max_iterations=20, n_neighbors=7, contamination=0.3):
    i = 1
    normality_met = False
    best_model_params = ""
    final_transformation = ""
    coefficients = ""
    equation_parts = []
    Original = list(pd.DataFrame(series).columns)

    # Apply smoothing on the original series before transformation
    df_original = pd.DataFrame(series, columns=Original)
    #smoothed_series = smooth_outliers(df_original, n_neighbors=7, contamination=0.1)[Original[0]]
    smoothed_series = smooth_outliers(df_original, n_neighbors=n_neighbors, contamination=contamination)[Original[0]]

    while i <= max_iterations and not normality_met:
        #clear_output(wait=True)
        print(f"Iteration: {i}")

        # Transform the smoothed series
        transformed_series = smoothed_series**(1/i)
        print("Type of transformed series:", type(transformed_series))
        #display(Math(r'y = x^{(1/%d)}' % i))

        if transformed_series.empty or transformed_series.isna().any() or np.isinf(transformed_series).any():
            print("Transformed series contains invalid values (empty, NaN, or infinite). Adjusting the transformation.")
            if i==1:
              i +=1
            else:
              i += 2
            continue

        # Indicate stationarity decomposition
        decomposition_results = test_stationarity_decompose_and_acf(transformed_series, model='additive', freq=12)
        # Select the best model
        best_model = select_best_arima_auto(transformed_series, max_p=max_p, max_q=max_q)
        #Extracting the residuals
        residuals = best_model.resid()

        normal_params = check_residuals_normality(residuals)


        if normal_params:
            normality_met = True
            print(f"Normality assumption met at iteration {i}.")
            # Extract model parameters and coefficients for final output
            if best_model.order:
                p, d, q = best_model.order
                final_transformation = f"y^{{1/{i}}}"
                try:
                    coef_summary = best_model.summary().tables[1].as_html()
                    df = pd.read_html(coef_summary, header=0, index_col=0)[0]
                    intercept = df.loc['intercept', 'coef'] if 'intercept' in df.index else 0
                    equation_parts = [f"{intercept:.4f}"]
                    for j in range(1, p+1):
                        coef = df.loc[f'ar.L{j}', 'coef']
                        equation_parts.append(f" + {coef:.4f}y_{{t-{j}}}")
                    for j in range(1, q+1):
                        coef = df.loc[f'ma.L{j}', 'coef']
                        equation_parts.append(f" + {coef:.4f} \\epsilon_{{t-{j}}}")
                except Exception as e:
                    print("Failed to extract coefficients:", str(e))
                    coefficients = "Unable to extract coefficients due to unexpected format."
        else:
            print("Normality assumption not met, increasing transformation power.")

        if i == 1:
            i += 1
        else:
            i += 2

        mu = ""
        std = ""
        if normality_met:
            print("Assumptions met, process completed.")
            print("The final model is.")
            latex_string = f"The final model is {best_model.order} with transformation {final_transformation}"

            #display(print(best_model.summary()))
            print(best_model.summary())
            #best_model.plot_diagnostics(figsize=(10, 10))

            mu, std = normal_params if normal_params else (np.nan, np.nan)
            """
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
            sns.histplot(residuals, kde=True, stat='density', ax=ax1)
            ax1.set_title('Residuals Density')
            ax1.set_xlabel('Residuals')
            ax1.set_ylabel('Density')
        
            if normal_params:
                x = np.linspace(mu - 3*std, mu + 3*std, 100)
                p = norm.pdf(x, mu, std)
                ax1.plot(x, p, color='red')

            sns.ecdfplot(residuals, ax=ax2)
            ax2.set_title('Cumulative Distribution of Residuals')
            ax2.set_xlabel('Residuals')
            ax2.set_ylabel('Cumulative Probability')
            plt.tight_layout()
            # plt.show()
            """
        else:
            print("Failed to meet normality assumption after maximum iterations.")

    #return best_model,1/i,mu, std
    return best_model,1/i,normal_params, normality_met



# df = import_data_clim(1,179)
# # Example usage, replace 'df['PRECIPITATION']' with your actual series
# selected_model,power,mean, st_d = iterative_modeling(pd.to_numeric(df['prectotcorr']))