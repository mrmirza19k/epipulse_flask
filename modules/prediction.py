"""
EpiPulse AI - Module 3: Outbreak Prediction
ARIMA-based forecasting + simple LSTM-like neural network using sklearn
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional
import warnings
warnings.filterwarnings("ignore")


# ─── ARIMA-style Forecasting (via statsmodels if available, else fallback) ───

def arima_forecast(series: pd.Series, horizon: int = 14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Fit ARIMA model and forecast.
    Returns (forecast, lower_ci, upper_ci).
    """
    try:
        from statsmodels.tsa.arima.model import ARIMA
        model = ARIMA(series.values, order=(2, 1, 2))
        result = model.fit()
        forecast_obj = result.get_forecast(steps=horizon)
        mean = forecast_obj.predicted_mean
        ci = forecast_obj.conf_int(alpha=0.2)
        return (
            np.maximum(mean, 0),
            np.maximum(ci[:, 0], 0),
            np.maximum(ci[:, 1], 0)
        )
    except Exception:
        return _exponential_smoothing_forecast(series, horizon)


def _exponential_smoothing_forecast(series: pd.Series, horizon: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Fallback: Holt-Winters style exponential smoothing.
    """
    values = series.dropna().values
    if len(values) == 0:
        dummy = np.zeros(horizon)
        return dummy, dummy, dummy

    alpha = 0.3  # smoothing factor
    beta = 0.1   # trend factor

    # Initialize
    level = values[0]
    trend = np.mean(np.diff(values[:min(7, len(values))])) if len(values) > 1 else 0

    for v in values:
        prev_level = level
        level = alpha * v + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend

    forecast = np.array([max(0, level + i * trend) for i in range(1, horizon + 1)])
    std = np.std(values[-min(14, len(values)):]) if len(values) > 1 else 5
    lower = np.maximum(forecast - 1.96 * std, 0)
    upper = forecast + 1.96 * std
    return forecast, lower, upper


def prophet_style_forecast(series: pd.Series, dates: pd.Series,
                            horizon: int = 14) -> pd.DataFrame:
    """
    Prophet-inspired trend + seasonality decomposition forecast.
    Returns DataFrame with date, yhat, yhat_lower, yhat_upper.
    """
    values = series.values
    t = np.arange(len(values))

    # Fit linear trend
    if len(t) > 1:
        trend_coef = np.polyfit(t, values, 1)
        trend = np.poly1d(trend_coef)
    else:
        trend = lambda x: np.full_like(x, values[0], dtype=float)

    # Weekly seasonality
    week_effects = np.zeros(7)
    for i, v in enumerate(values):
        week_effects[i % 7] += v - trend(i)
    counts = np.bincount(np.arange(len(values)) % 7)
    week_effects = week_effects / np.maximum(counts, 1)

    # Forecast
    t_future = np.arange(len(values), len(values) + horizon)
    trend_future = np.maximum(trend(t_future), 0)
    seasonal_future = np.array([week_effects[i % 7] for i in t_future])
    yhat = np.maximum(trend_future + seasonal_future, 0)

    std = np.std(values[-14:]) if len(values) >= 14 else np.std(values) if len(values) > 1 else 5
    last_date = dates.max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon)

    return pd.DataFrame({
        "date": future_dates,
        "yhat": yhat,
        "yhat_lower": np.maximum(yhat - 1.645 * std, 0),
        "yhat_upper": yhat + 1.645 * std,
        "model": "Prophet-style"
    })


def rolling_lstm_forecast(series: pd.Series, horizon: int = 14,
                          lookback: int = 14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simple neural-network style forecast using rolling window regression.
    Simulates LSTM-like sequence modeling without deep learning dependency.
    """
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    values = series.dropna().values
    if len(values) < lookback + 5:
        return _exponential_smoothing_forecast(series, horizon)

    # Build supervised dataset
    X, y = [], []
    for i in range(lookback, len(values)):
        X.append(values[i - lookback:i])
        y.append(values[i])

    X, y = np.array(X), np.array(y)
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

    model = Ridge(alpha=1.0)
    model.fit(X_scaled, y_scaled)

    # Recursive forecast
    forecast = []
    window = list(values[-lookback:])
    for _ in range(horizon):
        x_in = np.array(window[-lookback:]).reshape(1, -1)
        x_scaled = scaler_X.transform(x_in)
        pred_scaled = model.predict(x_scaled)
        pred = float(scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0][0])
        pred = max(0, pred)
        forecast.append(pred)
        window.append(pred)

    forecast = np.array(forecast)
    std = np.std(values[-14:]) * 1.5
    return forecast, np.maximum(forecast - std, 0), forecast + std


def forecast_all_methods(series: pd.Series, dates: pd.Series,
                          horizon: int = 14) -> dict:
    """Run all forecasting methods and return combined results."""
    results = {}

    # ARIMA
    arima_mean, arima_lo, arima_hi = arima_forecast(series, horizon)
    results["ARIMA"] = {"mean": arima_mean, "lower": arima_lo, "upper": arima_hi}

    # Prophet-style
    prophet_df = prophet_style_forecast(series, dates, horizon)
    results["Prophet"] = {
        "mean": prophet_df["yhat"].values,
        "lower": prophet_df["yhat_lower"].values,
        "upper": prophet_df["yhat_upper"].values,
        "dates": prophet_df["date"].values
    }

    # LSTM-style
    lstm_mean, lstm_lo, lstm_hi = rolling_lstm_forecast(series, horizon)
    results["LSTM"] = {"mean": lstm_mean, "lower": lstm_lo, "upper": lstm_hi}

    # Ensemble: average of all three
    ensemble_mean = (arima_mean + results["Prophet"]["mean"] + lstm_mean) / 3
    ensemble_lo = (arima_lo + results["Prophet"]["lower"] + lstm_lo) / 3
    ensemble_hi = (arima_hi + results["Prophet"]["upper"] + lstm_hi) / 3
    results["Ensemble"] = {"mean": ensemble_mean, "lower": ensemble_lo, "upper": ensemble_hi}

    return results


def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Compute MAE, RMSE, MAPE evaluation metrics."""
    actual = np.array(actual)
    predicted = np.array(predicted)
    mask = ~np.isnan(actual) & ~np.isnan(predicted)
    actual, predicted = actual[mask], predicted[mask]

    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = np.mean(np.abs((actual - predicted) / np.maximum(actual, 1))) * 100

    return {
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE": round(mape, 2),
    }
