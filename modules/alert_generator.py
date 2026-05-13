"""
EpiPulse AI - Module 6: Automated Alert Generator
AI-style natural language alert summaries
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict


ALERT_LEVELS = {
    "Low":      {"emoji": "🟢", "color": "#2ecc71", "urgency": "Monitor"},
    "Moderate": {"emoji": "🟡", "color": "#f39c12", "urgency": "Watch"},
    "High":     {"emoji": "🟠", "color": "#e67e22", "urgency": "Alert"},
    "Critical": {"emoji": "🔴", "color": "#e74c3c", "urgency": "URGENT"},
}


def generate_alert_message(district: str, disease: str, risk_score: float,
                            risk_level: str, growth_rate: float,
                            avg_cases: float, env_score: float,
                            surge_estimate: str, latest_cases: int) -> str:
    """Generate a natural language alert message."""
    level_info = ALERT_LEVELS.get(risk_level, ALERT_LEVELS["Low"])
    emoji = level_info["emoji"]
    urgency = level_info["urgency"]

    # Growth description
    if growth_rate > 0.5:
        growth_desc = f"a sharp {growth_rate*100:.0f}% weekly rise"
    elif growth_rate > 0.2:
        growth_desc = f"a notable {growth_rate*100:.0f}% weekly increase"
    elif growth_rate > 0:
        growth_desc = f"a gradual {growth_rate*100:.0f}% weekly uptick"
    elif growth_rate < -0.1:
        growth_desc = f"a {abs(growth_rate)*100:.0f}% weekly decline"
    else:
        growth_desc = "stable case counts"

    # Environmental risk description
    if env_score > 75:
        env_desc = "highly favorable environmental conditions (elevated humidity and temperature)"
    elif env_score > 50:
        env_desc = "moderately elevated environmental risk factors"
    else:
        env_desc = "near-normal environmental conditions"

    # Build message
    message = (
        f"{emoji} [{urgency}] {disease} — {district} District\n\n"
        f"Current surveillance data shows {growth_desc} in {disease} cases "
        f"({latest_cases} cases reported in latest period, "
        f"averaging {avg_cases:.0f} cases/day). "
        f"Risk score: {risk_score:.0f}/100 ({risk_level}).\n\n"
        f"Environmental analysis indicates {env_desc}. "
        f"{'Outbreak conditions appear favorable — proactive containment recommended.' if env_score > 60 else 'Continue standard monitoring.'} "
        f"Projected surge window: {surge_estimate}.\n\n"
        f"Recommended actions: {'⚡ Issue public health advisory, mobilize rapid response teams, increase hospital readiness.' if risk_level in ['High', 'Critical'] else '📋 Increase surveillance frequency, alert district health officers.'}"
    )
    return message


def generate_all_alerts(risk_df: pd.DataFrame, disease: str,
                         df_full: pd.DataFrame) -> List[Dict]:
    """Generate alerts for all districts based on risk scores."""
    alerts = []
    if risk_df.empty:
        return alerts

    from modules.risk_scoring import estimate_surge_days

    for _, row in risk_df.iterrows():
        if row["risk_score"] < 20:
            continue  # Skip very low risk

        growth_rate = 0.0
        if not df_full.empty:
            district_data = df_full[
                (df_full["district"] == row["district"]) &
                (df_full["disease"] == disease)
            ].sort_values("date")
            if not district_data.empty and "growth_rate_7d" in district_data.columns:
                growth_rate = float(district_data["growth_rate_7d"].iloc[-1])

        surge = estimate_surge_days(row["risk_score"], growth_rate)
        msg = generate_alert_message(
            district=row["district"],
            disease=disease,
            risk_score=row["risk_score"],
            risk_level=row["risk_level"],
            growth_rate=growth_rate,
            avg_cases=row["avg_cases"],
            env_score=row.get("env_score", 50),
            surge_estimate=surge,
            latest_cases=row["latest_cases"]
        )

        alerts.append({
            "district": row["district"],
            "disease": disease,
            "risk_level": row["risk_level"],
            "risk_score": row["risk_score"],
            "message": msg,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "color": ALERT_LEVELS[row["risk_level"]]["color"],
            "emoji": ALERT_LEVELS[row["risk_level"]]["emoji"],
        })

    # Sort by risk score descending
    alerts.sort(key=lambda x: x["risk_score"], reverse=True)
    return alerts


def get_system_status_summary(alerts: List[Dict]) -> Dict:
    """Get a high-level system status from all active alerts."""
    if not alerts:
        return {"level": "Normal", "message": "No significant outbreaks detected. All districts nominal.", "color": "#2ecc71"}

    max_risk = max(a["risk_score"] for a in alerts)
    critical_count = sum(1 for a in alerts if a["risk_level"] == "Critical")
    high_count = sum(1 for a in alerts if a["risk_level"] == "High")

    if critical_count > 0:
        return {
            "level": "CRITICAL",
            "message": f"{critical_count} district(s) at CRITICAL outbreak risk. Immediate intervention required.",
            "color": "#e74c3c"
        }
    elif high_count > 0:
        return {
            "level": "HIGH ALERT",
            "message": f"{high_count} district(s) at HIGH outbreak risk. Enhanced surveillance activated.",
            "color": "#e67e22"
        }
    elif max_risk >= 30:
        return {
            "level": "WATCH",
            "message": f"{len(alerts)} district(s) showing elevated disease activity. Monitoring closely.",
            "color": "#f39c12"
        }
    else:
        return {
            "level": "Normal",
            "message": "All districts within normal disease activity thresholds.",
            "color": "#2ecc71"
        }
