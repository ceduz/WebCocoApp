import numpy as np
import pandas as pd
from .modelling import smooth_outliers
#import matplotlib.pyplot as plt
from scipy.stats import truncnorm

def forecast_scenarios(model, steps=15, n_scenarios=500, power=1, alpha=0.05, mean=0, std=1):
    """
    Generates forecast scenarios from a fitted pmdarima ARIMA model, applies inverse transformation,
    and reshapes the output DataFrame using truncated normal distribution for noise.

    Parameters:
    - model: A fitted pmdarima.arima.arima.ARIMA model.
    - steps: Number of forecast steps ahead.
    - n_scenarios: Number of scenarios to simulate.
    - power: The power transformation applied to the original data (to perform inverse transformation).
    - alpha: Significance level for the prediction intervals.
    - mean: Mean of the truncated normal distribution.
    - std: Standard deviation of the truncated normal distribution.

    Returns:
    - forecasts_df: DataFrame containing forecasted scenarios, transposed for periods as rows.
    """
    # Ensure the model is fitted
    if not hasattr(model, 'arima_res_'):
        raise ValueError("The ARIMA model must be fitted before forecasting.")

    mean = float(mean)
    std = float(std)
    power = float(power)

    # Calculate bounds for a truncated normal distribution
    lower_bound = mean - 2 * std  # Two sigma below the mean
    upper_bound = mean + 2 * std  # Two sigma above the mean

    # Generate forecasts
    forecasts = np.zeros((n_scenarios, steps))
    for i in range(n_scenarios):
        forecast_result = model.predict(n_periods=steps, return_conf_int=False)
        # Generate truncated noise
        noise = truncnorm.rvs((lower_bound - mean) / std, (upper_bound - mean) / std, loc=mean, scale=std, size=steps)
        forecasts[i, :] = forecast_result + noise

    # Inverse transformation
    if power != 1:
        forecasts = np.power(forecasts, 1/power)

    # Convert forecasts to DataFrame and transpose
    forecasts_df = pd.DataFrame(forecasts, columns=[f'S{i+1}' for i in range(steps)])
    forecasts_df = forecasts_df.transpose()  # Transpose so that periods are rows and scenarios are columns

    # Plot the forecasts
    """
    plt.figure(figsize=(10, 6))
    for i in range(n_scenarios):
        plt.plot(forecasts_df.index, forecasts_df.iloc[:, i], color='blue', alpha=0.05)
    plt.title('Forecast Scenarios')
    plt.xlabel('Time Steps Ahead')
    plt.ylabel('Forecast Value')
    plt.show()
    """

    return forecasts_df