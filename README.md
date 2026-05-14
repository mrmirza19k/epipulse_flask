# 🦠 EpiPulse AI — Outbreak Surveillance Dashboard

> **Intelligent Disease Outbreak Early Trend Analyzer**  
> Real-time epidemic surveillance powered by ARIMA forecasting, anomaly detection, and composite risk scoring — built on Flask + Vanilla JS + Plotly.js.

---

## 📸 Overview

EpiPulse AI is a full-stack web application for monitoring and predicting disease outbreaks across districts. It ingests daily case-level surveillance data, detects anomalies, forecasts multi-model outbreak trajectories, and generates automated risk alerts — all rendered in an interactive dark-themed dashboard.

**Tracked Diseases:** Dengue · Influenza · Malaria · COVID-19 · Chikungunya  
**Coverage Area:** 10 districts across Punjab (Ludhiana, Amritsar, Jalandhar, Patiala, Sangrur, Bathinda, Mohali, Hoshiarpur, Gurdaspur, Firozpur)

---

## ✨ Features

- **Multi-Model Forecasting** — ARIMA (via statsmodels), Prophet-style trend, LSTM-like neural net (sklearn), and Ensemble with confidence intervals
- **Anomaly Detection** — Z-score, IQR, Isolation Forest, and STL decomposition for outbreak spike detection
- **Composite Risk Scoring** — Weighted risk engine across trend velocity, environmental factors, geographic density, and anomaly flags
- **Automated Alerts** — Natural language alert summaries with 4-tier urgency levels (🟢 Low → 🔴 Critical)
- **District Risk Map** — Geo-tagged risk visualization per district per disease
- **Interactive Chat Interface** — AI-style conversational query panel alongside the main dashboard
- **Synthetic Data Generator** — Realistic epidemic data with seasonal patterns and Gaussian outbreak bursts for demo/testing

---

## 🗂️ Project Structure

```
EpiPulse/
├── app.py                        # Flask backend & API routes
├── requirements.txt
├── README.md
├── data/
│   ├── generate_data.py          # Synthetic epidemic data generator
│   └── epidemic_data.csv         # Generated/cached dataset
├── modules/
│   ├── __init__.py
│   ├── preprocessing.py          # Data cleaning, rolling averages, lag features
│   ├── anomaly_detection.py      # Z-score, IQR, Isolation Forest, STL
│   ├── prediction.py             # ARIMA, LSTM-like, Ensemble forecasting
│   ├── risk_scoring.py           # Composite outbreak risk engine
│   └── alert_generator.py        # NL alert message generator
├── static/
│   ├── css/
│   │   ├── style.css             # Main dark-theme dashboard styles
│   │   └── chat.css              # Chat panel styles
│   └── js/
│       ├── app.js                # Core frontend logic & Plotly charts
│       └── chat.js               # Chat interface controller
└── templates/
    └── index.html                # Main Jinja2 template
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# 1. Clone the repository
git clone (https://github.com/mrmirza19k/epipulse_flask).git
cd epipulse_flask

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask development server
python app.py
```

Open your browser at **http://localhost:5000**

> **Note:** On first launch, EpiPulse auto-generates `data/epidemic_data.csv` with 180 days of synthetic surveillance data across all districts and diseases. Subsequent launches reuse the cached file.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Renders the main dashboard |
| `GET` | `/api/meta` | Available diseases, districts, and date range |
| `GET` | `/api/summary` | Aggregated summary statistics (supports `?start=&end=`) |
| `GET` | `/api/trends` | Time-series cases + anomaly summary (`?district=&disease=&start=&end=`) |
| `GET` | `/api/forecast` | Multi-model forecasts + backtesting metrics (`?district=&disease=&horizon=14`) |
| `GET` | `/api/risk` | District-level risk map with geo-coordinates (`?disease=`) |
| `GET` | `/api/alerts` | Auto-generated NL alert messages per district/disease |
| `GET` | `/api/status` | System-level status summary |

---

## 🧠 Module Details

### `modules/preprocessing.py`
Cleans raw case data, generates rolling averages (7-day, 14-day), computes lag features, and extracts district-disease time-series slices.

### `modules/anomaly_detection.py`
Runs four detection strategies in parallel:
- **Z-score** — flags values beyond a configurable σ threshold
- **IQR** — interquartile-range-based spike detection
- **Isolation Forest** — unsupervised ML outlier isolation (scikit-learn)
- **STL Decomposition** — seasonal-trend decomposition residual analysis

### `modules/prediction.py`
Implements multi-model outbreak forecasting with backtesting:
- **ARIMA(2,1,2)** via `statsmodels` (falls back to linear trend on failure)
- **LSTM-like** sequence model using `sklearn` MLPRegressor with sliding windows
- **Ensemble** — weighted average of ARIMA + LSTM outputs

### `modules/risk_scoring.py`
Computes a 0–100 composite risk score per district-disease pair:

| Factor | Weight |
|--------|--------|
| Case growth rate trend | 35% |
| Environmental (humidity, rainfall, temperature) | 25% |
| Geographic / population density | 20% |
| Anomaly detection flags | 20% |

Risk levels: **Low** (0–30) · **Moderate** (30–60) · **High** (60–80) · **Critical** (80–100)

### `modules/alert_generator.py`
Generates human-readable outbreak alerts with urgency labels, emoji indicators, growth statistics, surge estimates, and recommended actions per district/disease combination.

---

## 🎨 Frontend Stack

| Technology | Role |
|------------|------|
| **Jinja2** | Server-side HTML templating |
| **Plotly.js 2.32** | Interactive time-series, forecast, and risk charts |
| **Space Grotesk** | UI font |
| **JetBrains Mono** | Monospace / data font |
| **Vanilla JS** | State management, API calls, chart rendering |

The dashboard uses a custom dark design system with CSS variables:
- Background: `#070d17` · Card: `#0d1b2a` · Primary: `#00d4ff`
- Risk palette: Low `#2ecc71` · Moderate `#f39c12` · High `#e67e22` · Critical `#e74c3c`

---

## 📊 Synthetic Data Schema

The data generator produces records with the following fields:

| Column | Type | Description |
|--------|------|-------------|
| `date` | datetime | Daily observation date |
| `district` | str | Punjab district name |
| `disease` | str | Disease name |
| `cases` | int | Daily confirmed cases |
| `hospitalizations` | int | Daily hospitalizations |
| `tests_conducted` | int | Tests performed |
| `positive_rate` | float | Positivity rate (%) |
| `temperature` | float | Daily avg temperature (°C) |
| `humidity` | float | Relative humidity (%) |
| `rainfall_mm` | float | Rainfall in mm |
| `population` | int | District population |
| `population_density` | float | People per km² |

---

## ⚙️ Configuration

All major parameters are set as constants at the top of each module:

- **Forecast horizon:** `horizon` query param (default: 14 days)
- **ARIMA order:** `(2, 1, 2)` in `prediction.py`
- **Risk weights:** `WEIGHTS` dict in `risk_scoring.py`
- **Anomaly thresholds:** `threshold` param in `anomaly_detection.py`
- **Data generation:** `days=180`, `seed=42` in `generate_data.py`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [statsmodels](https://www.statsmodels.org/) — ARIMA implementation
- [scikit-learn](https://scikit-learn.org/) — Isolation Forest & MLP
- [Plotly.js](https://plotly.com/javascript/) — Interactive charting
- [Flask](https://flask.palletsprojects.com/) — Web framework
