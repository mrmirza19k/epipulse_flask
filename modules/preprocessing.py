"""
EpiPulse AI - Module 1: Data Preprocessing
Handles cleaning, feature engineering, rolling averages, lag features
"""
import pandas as pd
import numpy as np
from typing import Tuple


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Full preprocessing pipeline."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = _fill_missing(df)
    df = _normalize_cases(df)
    df = _add_lag_features(df)
    df = _add_rolling_features(df)
    df = _add_seasonality(df)
    df = _add_growth_rate(df)
    return df


def _fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing values per district-disease group."""
    numeric_cols = ["cases", "hospitalizations", "tests_conducted",
                    "temperature", "humidity", "rainfall_mm"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df.groupby(["district", "disease"])[col].transform(
                lambda x: x.fillna(x.rolling(7, min_periods=1).mean())
            )
    return df


def _normalize_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize cases per 100k population."""
    df["cases_per_100k"] = (df["cases"] / df["population"] * 100_000).round(3)
    return df


def _add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag features: t-7, t-14, t-21."""
    for lag in [7, 14, 21]:
        df[f"cases_lag_{lag}"] = df.groupby(["district", "disease"])["cases"].shift(lag)
    return df


def _add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add 7-day and 14-day rolling averages and std."""
    for window in [7, 14]:
        df[f"rolling_avg_{window}d"] = df.groupby(["district", "disease"])["cases"].transform(
            lambda x: x.rolling(window, min_periods=1).mean().round(2)
        )
        df[f"rolling_std_{window}d"] = df.groupby(["district", "disease"])["cases"].transform(
            lambda x: x.rolling(window, min_periods=1).std().fillna(0).round(2)
        )
    return df


def _add_seasonality(df: pd.DataFrame) -> pd.DataFrame:
    """Add week-of-year and month seasonality indicators."""
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_monsoon"] = df["month"].between(6, 9).astype(int)
    df["sin_week"] = np.sin(2 * np.pi * df["week_of_year"] / 52).round(4)
    df["cos_week"] = np.cos(2 * np.pi * df["week_of_year"] / 52).round(4)
    return df


def _add_growth_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Add week-over-week growth rate."""
    df["growth_rate_7d"] = df.groupby(["district", "disease"])["cases"].pct_change(7).round(4)
    df["growth_rate_7d"] = df["growth_rate_7d"].replace([np.inf, -np.inf], 0).fillna(0)
    return df


def get_district_disease_series(df: pd.DataFrame, district: str, disease: str) -> pd.DataFrame:
    """Extract and return time series for a specific district and disease."""
    mask = (df["district"] == district) & (df["disease"] == disease)
    series = df[mask].sort_values("date").reset_index(drop=True)
    return series


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Compute summary statistics for the dashboard."""
    latest_date = df["date"].max()
    recent = df[df["date"] >= latest_date - pd.Timedelta(days=7)]
    prev = df[(df["date"] >= latest_date - pd.Timedelta(days=14)) &
              (df["date"] < latest_date - pd.Timedelta(days=7))]

    total_recent = recent["cases"].sum()
    total_prev = prev["cases"].sum()
    delta_pct = ((total_recent - total_prev) / max(total_prev, 1)) * 100

    return {
        "total_cases_7d": int(total_recent),
        "change_pct": round(delta_pct, 1),
        "active_districts": int(recent[recent["cases"] > 0]["district"].nunique()),
        "total_hospitalizations_7d": int(recent["hospitalizations"].sum()),
        "highest_risk_district": recent.groupby("district")["cases"].sum().idxmax(),
        "most_active_disease": recent.groupby("disease")["cases"].sum().idxmax(),
    }
