"""
EpiPulse AI - Flask Backend
Intelligent Disease Outbreak Early Trend Analyzer
"""
from flask import Flask, jsonify, render_template, request
import pandas as pd
import numpy as np
import sys, os, warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(__file__))

from data.generate_data import load_or_generate
from modules.preprocessing import preprocess, get_district_disease_series, get_summary_stats
from modules.anomaly_detection import run_full_anomaly_detection, get_anomaly_summary
from modules.prediction import forecast_all_methods, compute_metrics
from modules.risk_scoring import compute_district_risk_map, DISTRICT_COORDS, estimate_surge_days
from modules.alert_generator import generate_all_alerts, get_system_status_summary

app = Flask(__name__)

# ─── DATA LOADING ────────────────────────────────────────────────────────────
_df_cache = None

def get_df():
    global _df_cache
    if _df_cache is None:
        df_raw = load_or_generate("data/epidemic_data.csv")
        df = preprocess(df_raw)
        df = run_full_anomaly_detection(df)
        _df_cache = df
    return _df_cache

def df_to_safe(df):
    """Convert DataFrame to JSON-safe dict."""
    df = df.copy()
    for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d")
    return df.replace([np.inf, -np.inf], None).where(pd.notnull(df), None).to_dict(orient="records")


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/meta")
def api_meta():
    df = get_df()
    return jsonify({
        "diseases": sorted(df["disease"].unique().tolist()),
        "districts": sorted(df["district"].unique().tolist()),
        "date_min": df["date"].min().strftime("%Y-%m-%d"),
        "date_max": df["date"].max().strftime("%Y-%m-%d"),
    })


@app.route("/api/summary")
def api_summary():
    df = get_df()
    start = request.args.get("start")
    end = request.args.get("end")
    if start and end:
        df = df[(df["date"] >= start) & (df["date"] <= end)]
    stats = get_summary_stats(df)
    return jsonify(stats)


@app.route("/api/trends")
def api_trends():
    df = get_df()
    district = request.args.get("district", "Ludhiana")
    disease = request.args.get("disease", "Dengue")
    start = request.args.get("start")
    end = request.args.get("end")
    if start and end:
        df = df[(df["date"] >= start) & (df["date"] <= end)]

    series = get_district_disease_series(df, district, disease)
    anomaly_summary = get_anomaly_summary(df[df["disease"] == disease])
    return jsonify({
        "series": df_to_safe(series),
        "anomaly_summary": df_to_safe(anomaly_summary),
    })


@app.route("/api/forecast")
def api_forecast():
    df = get_df()
    district = request.args.get("district", "Ludhiana")
    disease = request.args.get("disease", "Dengue")
    horizon = int(request.args.get("horizon", 14))
    start = request.args.get("start")
    end = request.args.get("end")
    if start and end:
        df = df[(df["date"] >= start) & (df["date"] <= end)]

    series_df = get_district_disease_series(df, district, disease)
    if len(series_df) < 15:
        return jsonify({"error": "Not enough data"}), 400

    forecasts = forecast_all_methods(series_df["cases"], series_df["date"], horizon)

    future_dates = pd.date_range(
        start=series_df["date"].max() + pd.Timedelta(days=1),
        periods=horizon
    ).strftime("%Y-%m-%d").tolist()

    result = {
        "future_dates": future_dates,
        "historical_dates": series_df["date"].tail(60).dt.strftime("%Y-%m-%d").tolist(),
        "historical_cases": series_df["cases"].tail(60).tolist(),
        "models": {},
        "metrics": {},
    }
    for model_name, data in forecasts.items():
        result["models"][model_name] = {
            "mean": [round(float(v), 1) for v in data["mean"]],
            "lower": [round(float(v), 1) for v in data["lower"]],
            "upper": [round(float(v), 1) for v in data["upper"]],
        }

    # Backtesting metrics
    if len(series_df) >= horizon * 2:
        split = len(series_df) - horizon
        train = series_df["cases"].iloc[:split]
        actual = series_df["cases"].iloc[split:].values
        test_fc = forecast_all_methods(train, series_df["date"].iloc[:split], horizon)
        for model_name, data in test_fc.items():
            result["metrics"][model_name] = compute_metrics(actual, data["mean"])

    return jsonify(result)


@app.route("/api/risk")
def api_risk():
    df = get_df()
    disease = request.args.get("disease", "Dengue")
    start = request.args.get("start")
    end = request.args.get("end")
    if start and end:
        df = df[(df["date"] >= start) & (df["date"] <= end)]

    risk_df = compute_district_risk_map(df, disease)
    # Add coordinates
    if not risk_df.empty:
        risk_df["lat"] = risk_df["district"].map(lambda d: DISTRICT_COORDS.get(d, (30.9, 75.8))[0])
        risk_df["lon"] = risk_df["district"].map(lambda d: DISTRICT_COORDS.get(d, (30.9, 75.8))[1])

    return jsonify(df_to_safe(risk_df))


@app.route("/api/alerts")
def api_alerts():
    df = get_df()
    disease = request.args.get("disease", "Dengue")
    start = request.args.get("start")
    end = request.args.get("end")
    if start and end:
        df = df[(df["date"] >= start) & (df["date"] <= end)]

    risk_df = compute_district_risk_map(df, disease)
    alerts = generate_all_alerts(risk_df, disease, df)
    system_status = get_system_status_summary(alerts)

    # Cross-disease overview
    all_risks = []
    for d in sorted(df["disease"].unique()):
        rdf = compute_district_risk_map(df, d)
        if not rdf.empty:
            rdf["disease"] = d
            all_risks.append(rdf[["district", "disease", "risk_score"]].to_dict(orient="records"))

    return jsonify({
        "alerts": alerts,
        "system_status": system_status,
        "cross_disease": all_risks,
    })


@app.route("/api/analytics")
def api_analytics():
    df = get_df()
    disease = request.args.get("disease", "Dengue")
    start = request.args.get("start")
    end = request.args.get("end")
    if start and end:
        df = df[(df["date"] >= start) & (df["date"] <= end)]

    # Disease totals
    disease_totals = df.groupby("disease")["cases"].sum().reset_index()
    
    # Monthly trend
    monthly = df.copy()
    monthly["month_year"] = monthly["date"].dt.to_period("M").astype(str)
    monthly_agg = monthly.groupby(["month_year", "disease"])["cases"].sum().reset_index()

    # Correlation matrix
    corr_cols = ["cases", "temperature", "humidity", "rainfall_mm", "population_density"]
    avail = [c for c in corr_cols if c in df.columns]
    corr_matrix = df[avail].corr().round(3).to_dict()

    # Hospital burden
    hosp_df = df.groupby("district").agg(
        total_cases=("cases", "sum"),
        total_hosp=("hospitalizations", "sum")
    ).reset_index()
    hosp_df["hosp_rate"] = (hosp_df["total_hosp"] / hosp_df["total_cases"] * 100).round(1)

    # Positivity rate trend
    pos_rate = df.groupby("date")["positive_rate"].mean().reset_index()

    return jsonify({
        "disease_totals": df_to_safe(disease_totals),
        "monthly_trend": df_to_safe(monthly_agg),
        "corr_matrix": corr_matrix,
        "corr_labels": avail,
        "hospital_burden": df_to_safe(hosp_df),
        "positivity_rate": df_to_safe(pos_rate),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
