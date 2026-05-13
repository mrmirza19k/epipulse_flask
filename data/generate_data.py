"""
EpiPulse AI - Synthetic Data Generator
Generates realistic epidemic surveillance data for demo/testing
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

DISTRICTS = [
    "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Sangrur",
    "Bathinda", "Mohali", "Hoshiarpur", "Gurdaspur", "Firozpur"
]

DISEASES = ["Dengue", "Influenza", "Malaria", "COVID-19", "Chikungunya"]

POPULATION = {
    "Ludhiana": 3695000, "Amritsar": 2490000, "Jalandhar": 2181000,
    "Patiala": 1892000, "Sangrur": 1654000, "Bathinda": 1388000,
    "Mohali": 994628, "Hoshiarpur": 1586000, "Gurdaspur": 2299000,
    "Firozpur": 2027000
}


def generate_epidemic_data(days: int = 180, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic daily case data with realistic outbreak patterns."""
    np.random.seed(seed)
    records = []
    start_date = datetime.now() - timedelta(days=days)

    for district in DISTRICTS:
        for disease in DISEASES:
            base_cases = np.random.randint(5, 30)
            outbreak_day = np.random.randint(60, 140)
            outbreak_duration = np.random.randint(20, 40)
            outbreak_peak = np.random.randint(50, 200)

            for d in range(days):
                date = start_date + timedelta(days=d)

                # Seasonal component
                seasonal = 1 + 0.3 * np.sin(2 * np.pi * d / 365)

                # Outbreak component (Gaussian bump)
                dist_from_peak = d - outbreak_day
                if 0 <= dist_from_peak <= outbreak_duration:
                    outbreak_factor = outbreak_peak * np.exp(
                        -0.5 * ((dist_from_peak - outbreak_duration / 2) / (outbreak_duration / 4)) ** 2
                    )
                else:
                    outbreak_factor = 0

                # Environmental factors
                temp = 25 + 10 * np.sin(2 * np.pi * d / 365) + np.random.normal(0, 2)
                humidity = 60 + 20 * np.sin(2 * np.pi * (d - 30) / 365) + np.random.normal(0, 5)
                rainfall = max(0, 5 * np.sin(2 * np.pi * (d - 60) / 365) + np.random.normal(0, 3))

                # Final case count with noise
                cases = int(
                    max(0, (base_cases * seasonal + outbreak_factor) * (1 + np.random.normal(0, 0.15)))
                )
                hospitalizations = int(cases * np.random.uniform(0.1, 0.25))
                tests = int(cases * np.random.uniform(2, 5))

                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "district": district,
                    "disease": disease,
                    "cases": cases,
                    "hospitalizations": hospitalizations,
                    "tests_conducted": tests,
                    "positive_rate": round(cases / max(tests, 1) * 100, 2),
                    "temperature": round(temp, 1),
                    "humidity": round(max(0, min(100, humidity)), 1),
                    "rainfall_mm": round(rainfall, 1),
                    "population": POPULATION[district],
                    "population_density": round(POPULATION[district] / np.random.uniform(800, 3000), 1)
                })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["district", "disease", "date"]).reset_index(drop=True)
    return df


def load_or_generate(filepath: str = "data/epidemic_data.csv") -> pd.DataFrame:
    """Load existing data or generate new synthetic data."""
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, parse_dates=["date"])
        return df
    df = generate_epidemic_data()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    return df


if __name__ == "__main__":
    df = generate_epidemic_data()
    df.to_csv("data/epidemic_data.csv", index=False)
    print(f"Generated {len(df)} records across {df['district'].nunique()} districts "
          f"and {df['disease'].nunique()} diseases")
    print(df.head())
