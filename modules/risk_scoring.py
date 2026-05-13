"""
EpiPulse AI - Module 4: Risk Scoring Engine
Composite outbreak risk score with weighted factors
"""
import pandas as pd
import numpy as np
from typing import Dict


# Risk level thresholds
RISK_THRESHOLDS = {
    "Low": (0, 30),
    "Moderate": (30, 60),
    "High": (60, 80),
    "Critical": (80, 100)
}

# Weights for composite risk formula
WEIGHTS = {
    "trend": 0.35,       # Case growth rate trend
    "environment": 0.25, # Environmental factors (humidity, rainfall, temp)
    "geo": 0.20,         # Geographic / population density
    "anomaly": 0.20      # Anomaly detection flags
}


def normalize_to_score(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-100 scale."""
    if max_val == min_val:
        return 50.0
    return float(np.clip((value - min_val) / (max_val - min_val) * 100, 0, 100))


def compute_trend_score(growth_rate: float, rolling_avg: float,
                         base_avg: float) -> float:
    """Score based on case growth rate and trend direction."""
    # Growth rate component (0-100)
    growth_component = min(max(growth_rate * 100, -100), 200)  # cap extremes
    growth_score = normalize_to_score(growth_component, -50, 200)

    # Ratio of recent to historical average
    ratio = rolling_avg / max(base_avg, 1)
    ratio_score = normalize_to_score(ratio, 0.5, 5.0)

    return (growth_score * 0.6 + ratio_score * 0.4)


def compute_environment_score(humidity: float, rainfall: float, temperature: float,
                               disease: str) -> float:
    """Score based on environmental favorability for specific disease."""
    base = 0.0

    # Disease-specific optimal conditions
    disease_params = {
        "Dengue":       {"temp": (28, 35), "humidity": (70, 90), "rain": (10, 50)},
        "Malaria":      {"temp": (24, 32), "humidity": (60, 85), "rain": (5, 40)},
        "Chikungunya":  {"temp": (26, 34), "humidity": (65, 90), "rain": (8, 45)},
        "Influenza":    {"temp": (5, 15),  "humidity": (40, 60), "rain": (0, 10)},
        "COVID-19":     {"temp": (10, 20), "humidity": (40, 65), "rain": (0, 15)},
    }

    params = disease_params.get(disease, {
        "temp": (20, 35), "humidity": (50, 80), "rain": (5, 30)
    })

    # Temperature: closer to optimal range = higher score
    t_lo, t_hi = params["temp"]
    t_center = (t_lo + t_hi) / 2
    t_range = (t_hi - t_lo) / 2
    temp_score = max(0, 100 - abs(temperature - t_center) / max(t_range, 1) * 50)

    # Humidity
    h_lo, h_hi = params["humidity"]
    h_center = (h_lo + h_hi) / 2
    h_range = (h_hi - h_lo) / 2
    hum_score = max(0, 100 - abs(humidity - h_center) / max(h_range, 1) * 50)

    # Rainfall
    r_lo, r_hi = params["rain"]
    if r_lo <= rainfall <= r_hi:
        rain_score = 100.0
    elif rainfall < r_lo:
        rain_score = max(0, 100 - (r_lo - rainfall) * 5)
    else:
        rain_score = max(0, 100 - (rainfall - r_hi) * 3)

    return (temp_score * 0.35 + hum_score * 0.40 + rain_score * 0.25)


def compute_geo_score(population_density: float, cases_per_100k: float) -> float:
    """Score based on population density and case incidence rate."""
    density_score = normalize_to_score(population_density, 200, 15000)
    incidence_score = normalize_to_score(cases_per_100k, 0, 50)
    return (density_score * 0.4 + incidence_score * 0.6)


def compute_anomaly_score_component(anomaly_score: int) -> float:
    """Convert anomaly flags (0-3) to 0-100 score."""
    return (anomaly_score / 3.0) * 100


def compute_outbreak_risk(row: pd.Series, disease: str, base_avg: float) -> Dict:
    """
    Compute composite outbreak risk score for a single data point.
    Risk Score = Σ(weight_i × component_score_i)
    """
    trend_score = compute_trend_score(
        row.get("growth_rate_7d", 0),
        row.get("rolling_avg_7d", row["cases"]),
        base_avg
    )

    env_score = compute_environment_score(
        row.get("humidity", 65),
        row.get("rainfall_mm", 10),
        row.get("temperature", 28),
        disease
    )

    geo_score = compute_geo_score(
        row.get("population_density", 1000),
        row.get("cases_per_100k", 5)
    )

    anomaly_comp = compute_anomaly_score_component(
        int(row.get("anomaly_score", 0))
    )

    composite = (
        WEIGHTS["trend"] * trend_score +
        WEIGHTS["environment"] * env_score +
        WEIGHTS["geo"] * geo_score +
        WEIGHTS["anomaly"] * anomaly_comp
    )
    composite = round(min(max(composite, 0), 100), 1)

    # Determine risk level
    risk_level = "Low"
    for level, (lo, hi) in RISK_THRESHOLDS.items():
        if lo <= composite < hi:
            risk_level = level
            break

    return {
        "risk_score": composite,
        "risk_level": risk_level,
        "trend_score": round(trend_score, 1),
        "env_score": round(env_score, 1),
        "geo_score": round(geo_score, 1),
        "anomaly_score_component": round(anomaly_comp, 1)
    }


def compute_district_risk_map(df: pd.DataFrame, disease: str,
                               date_window: int = 7) -> pd.DataFrame:
    """
    Compute risk scores for all districts for a given disease.
    Returns DataFrame with one row per district, with risk scores.
    """
    latest = df["date"].max()
    recent = df[
        (df["disease"] == disease) &
        (df["date"] >= latest - pd.Timedelta(days=date_window))
    ].copy()

    if recent.empty:
        return pd.DataFrame()

    # Global baseline average
    all_avgs = df[df["disease"] == disease].groupby("district")["cases"].mean()

    records = []
    for district, group in recent.groupby("district"):
        # Use latest row for snapshot
        latest_row = group.sort_values("date").iloc[-1]
        base = float(all_avgs.get(district, group["cases"].mean()))
        risk_info = compute_outbreak_risk(latest_row, disease, base)

        records.append({
            "district": district,
            "total_cases_7d": int(group["cases"].sum()),
            "avg_cases": round(float(group["cases"].mean()), 1),
            "latest_cases": int(latest_row["cases"]),
            "population": int(latest_row.get("population", 1_000_000)),
            **risk_info
        })

    risk_df = pd.DataFrame(records).sort_values("risk_score", ascending=False)
    return risk_df


def estimate_surge_days(risk_score: float, growth_rate: float) -> str:
    """Estimate days until potential surge based on risk metrics."""
    if risk_score < 30:
        return "No surge expected"
    elif risk_score < 60:
        days = int(30 - growth_rate * 20)
        return f"~{max(days, 15)} days"
    elif risk_score < 80:
        days = int(20 - growth_rate * 15)
        return f"~{max(days, 8)} days"
    else:
        days = int(10 - growth_rate * 10)
        return f"~{max(days, 3)} days (URGENT)"


DISTRICT_COORDS = {
    "Ludhiana":   (30.9010, 75.8573),
    "Amritsar":   (31.6340, 74.8723),
    "Jalandhar":  (31.3260, 75.5762),
    "Patiala":    (30.3398, 76.3869),
    "Sangrur":    (30.2454, 75.8440),
    "Bathinda":   (30.2070, 74.9455),
    "Mohali":     (30.7046, 76.7179),
    "Hoshiarpur": (31.5330, 75.9110),
    "Gurdaspur":  (32.0398, 75.4087),
    "Firozpur":   (30.9285, 74.6096),
}
