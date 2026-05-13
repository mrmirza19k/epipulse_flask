"""
EpiPulse AI - Module 2: Trend & Anomaly Detection
Z-score, IQR, Isolation Forest, STL decomposition
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Tuple, List


def detect_zscore_anomalies(series: pd.Series, window: int = 14, threshold: float = 2.0) -> pd.Series:
    """
    Detect anomalies using rolling Z-score.
    Returns boolean Series: True = anomaly detected.
    """
    rolling_mean = series.rolling(window=window, min_periods=3).mean()
    rolling_std = series.rolling(window=window, min_periods=3).std()
    z_scores = (series - rolling_mean) / rolling_std.replace(0, np.nan)
    return z_scores.fillna(0).abs() > threshold, z_scores.fillna(0)


def detect_iqr_anomalies(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """
    Detect anomalies using IQR method.
    Returns boolean Series: True = outlier.
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    upper_bound = Q3 + multiplier * IQR
    lower_bound = Q1 - multiplier * IQR
    return (series > upper_bound) | (series < lower_bound)


def detect_isolation_forest(df: pd.DataFrame, features: List[str],
                             contamination: float = 0.05) -> np.ndarray:
    """
    Multivariate anomaly detection using Isolation Forest.
    Returns array: -1 = anomaly, 1 = normal.
    """
    df_feat = df[features].copy().fillna(0)
    scaler = StandardScaler()
    X = scaler.fit_transform(df_feat)
    clf = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    return clf.fit_predict(X)


def stl_trend_extraction(series: pd.Series, period: int = 7) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Simplified STL-like decomposition using rolling stats.
    Returns (trend, seasonal, residual) components.
    """
    trend = series.rolling(window=period, center=True, min_periods=1).mean()
    detrended = series - trend
    # Seasonal: average by day of week
    day_of_week = pd.Series(range(len(series))) % period
    seasonal_avg = detrended.groupby(day_of_week).transform("mean")
    residual = detrended - seasonal_avg
    return trend, seasonal_avg, residual


def run_full_anomaly_detection(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all anomaly detection methods on the dataframe.
    Adds columns: anomaly_zscore, anomaly_iqr, anomaly_iforest, anomaly_combined
    """
    df = df.copy()
    df = df.sort_values(["district", "disease", "date"])

    # Z-score per group
    z_flags = []
    z_scores_col = []
    for _, group in df.groupby(["district", "disease"]):
        flags, scores = detect_zscore_anomalies(group["cases"])
        z_flags.extend(flags.tolist())
        z_scores_col.extend(scores.tolist())

    df["anomaly_zscore"] = z_flags
    df["zscore_value"] = z_scores_col

    # IQR per group
    iqr_flags = []
    for _, group in df.groupby(["district", "disease"]):
        flags = detect_iqr_anomalies(group["cases"])
        iqr_flags.extend(flags.tolist())
    df["anomaly_iqr"] = iqr_flags

    # Isolation Forest (global, multivariate)
    features = ["cases", "temperature", "humidity", "rainfall_mm",
                 "rolling_avg_7d", "growth_rate_7d"]
    available = [f for f in features if f in df.columns]
    if len(available) >= 3:
        iso_preds = detect_isolation_forest(df, available)
        df["anomaly_iforest"] = iso_preds == -1
    else:
        df["anomaly_iforest"] = False

    # Combined: flagged by at least 2 methods
    df["anomaly_score"] = (
        df["anomaly_zscore"].astype(int) +
        df["anomaly_iqr"].astype(int) +
        df["anomaly_iforest"].astype(int)
    )
    df["anomaly_combined"] = df["anomaly_score"] >= 2

    return df


def get_anomaly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize anomalies by district and disease."""
    if "anomaly_combined" not in df.columns:
        return pd.DataFrame()
    anomalies = df[df["anomaly_combined"] == True]
    summary = (
        anomalies.groupby(["district", "disease"])
        .agg(
            total_anomalies=("anomaly_combined", "sum"),
            latest_anomaly=("date", "max"),
            max_cases=("cases", "max"),
            avg_zscore=("zscore_value", "mean")
        )
        .reset_index()
        .sort_values("total_anomalies", ascending=False)
    )
    summary["avg_zscore"] = summary["avg_zscore"].round(2)
    return summary
