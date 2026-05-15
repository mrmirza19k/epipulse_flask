# 🦠 EpiPulse AI — Intelligent Disease Outbreak Surveillance Dashboard

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge\&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_App-black?style=for-the-badge\&logo=flask)
![Machine Learning](https://img.shields.io/badge/AI%2FML-Forecasting-green?style=for-the-badge)
![Render](https://img.shields.io/badge/Deployment-Render-purple?style=for-the-badge)

Real-time epidemic surveillance powered by ARIMA forecasting, anomaly detection, and composite risk scoring — built on Flask + Vanilla JS + Plotly.js.

---

## 🌐 Live Demo

👉 [Open EpiPulse AI Dashboard](https://epipulse-flask.onrender.com/)

🔗 GitHub Repository: [https://github.com/mrmirza19k/epipulse_flask](https://github.com/mrmirza19k/epipulse_flask)

---

## 📌 Project Overview

EpiPulse AI is a full-stack AI-powered outbreak surveillance and forecasting platform designed to monitor disease trends, detect anomalies, predict future outbreaks, and generate automated health risk alerts.

The platform provides interactive analytics dashboards for tracking disease spread across multiple districts in Punjab using machine learning models, statistical forecasting, and intelligent risk analysis.

### 🎯 Key Objectives

* Predict disease outbreaks early
* Detect unusual spikes in cases
* Analyze district-level risks
* Generate automated health alerts
* Visualize epidemic trends interactively
* Support epidemic monitoring and healthcare analytics

---

## ✨ Features

### 📈 Multi-Model Forecasting

* ARIMA forecasting using statsmodels
* Prophet-style trend forecasting
* LSTM-like neural forecasting using sklearn
* Ensemble forecasting with confidence intervals

### 🚨 Anomaly Detection

* Z-score spike detection
* IQR-based anomaly detection
* Isolation Forest outlier detection
* STL decomposition residual analysis

### 🧠 Composite Risk Scoring

Weighted outbreak risk engine based on:

* Trend velocity
* Environmental factors
* Population density
* Anomaly detection flags

### 🔔 Automated Alerts

* Natural language outbreak alerts
* 4-tier urgency levels
* Suggested action recommendations

### 🗺️ District Risk Visualization

* Geo-tagged district-level monitoring
* Disease-specific risk analysis

### 💬 Interactive Chat Interface

AI-style conversational dashboard assistant integrated into the UI.

### 🧪 Synthetic Data Generator

Realistic epidemic data generation with:

* Seasonal patterns
* Gaussian outbreak bursts
* Environmental factors
* Multi-disease simulation

---

## 🧠 AI/ML Features

✅ ARIMA Forecasting
✅ Ensemble Prediction Models
✅ Isolation Forest Anomaly Detection
✅ Trend Analysis
✅ Composite Risk Engine
✅ Automated Alert Generation
✅ Time-Series Analytics

---

## 🛠 Tech Stack

| Technology          | Purpose            |
| ------------------- | ------------------ |
| Python              | Backend Logic      |
| Flask               | Web Framework      |
| Pandas              | Data Processing    |
| Scikit-Learn        | ML Algorithms      |
| Statsmodels         | ARIMA Forecasting  |
| Plotly.js           | Interactive Charts |
| HTML/CSS/JavaScript | Frontend           |
| Jinja2              | Templating Engine  |
| Render              | Deployment         |

---

## 📊 Supported Diseases

* Dengue
* Influenza
* Malaria
* COVID-19
* Chikungunya

---

## 📍 Coverage Area

Punjab Districts:

* Ludhiana
* Amritsar
* Jalandhar
* Patiala
* Sangrur
* Bathinda
* Mohali
* Hoshiarpur
* Gurdaspur
* Firozpur

---

## 📸 Project Screenshots

### Dashboard Overview

(Add Screenshot Here)

### Forecast Analytics

(Add Screenshot Here)

### Risk Monitoring

(Add Screenshot Here)

### Interactive Charts

image/Chatbot

---

## 🗂️ Project Structure

```bash
EpiPulse/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── generate_data.py
│   └── epidemic_data.csv
├── modules/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── anomaly_detection.py
│   ├── prediction.py
│   ├── risk_scoring.py
│   └── alert_generator.py
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── chat.css
│   └── js/
│       ├── app.js
│       └── chat.js
└── templates/
    └── index.html
```

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* pip

---

## ⚙️ Installation

```bash
git clone https://github.com/mrmirza19k/epipulse_flask.git

cd epipulse_flask

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Flask server
python app.py
```

Open your browser at:

```bash
http://localhost:5000
```

---

## 🔌 API Reference

| Method | Endpoint      | Description                    |
| ------ | ------------- | ------------------------------ |
| GET    | /             | Render dashboard               |
| GET    | /api/meta     | Diseases & districts metadata  |
| GET    | /api/summary  | Aggregated outbreak summary    |
| GET    | /api/trends   | Time-series trends & anomalies |
| GET    | /api/forecast | Forecast predictions           |
| GET    | /api/risk     | District-level risk map        |
| GET    | /api/alerts   | Generated outbreak alerts      |
| GET    | /api/status   | System status summary          |

---

## 🧩 Module Details

### modules/preprocessing.py

* Data cleaning
* Rolling averages
* Lag feature generation
* Time-series extraction

### modules/anomaly_detection.py

Implements:

* Z-score analysis
* IQR detection
* Isolation Forest
* STL decomposition

### modules/prediction.py

Forecasting models:

* ARIMA(2,1,2)
* LSTM-like MLPRegressor
* Ensemble forecasting

### modules/risk_scoring.py

Computes outbreak risk score based on:

| Factor                | Weight |
| --------------------- | ------ |
| Case Growth Trend     | 35%    |
| Environmental Factors | 25%    |
| Population Density    | 20%    |
| Anomaly Flags         | 20%    |

Risk Levels:

* Low (0–30)
* Moderate (30–60)
* High (60–80)
* Critical (80–100)

### modules/alert_generator.py

Generates:

* Human-readable alerts
* Urgency levels
* Growth statistics
* Recommended actions

---

## 📊 Synthetic Data Schema

| Column             | Type     | Description            |
| ------------------ | -------- | ---------------------- |
| date               | datetime | Daily observation date |
| district           | str      | Punjab district        |
| disease            | str      | Disease name           |
| cases              | int      | Daily cases            |
| hospitalizations   | int      | Daily hospitalizations |
| tests_conducted    | int      | Tests performed        |
| positive_rate      | float    | Positivity rate        |
| temperature        | float    | Average temperature    |
| humidity           | float    | Relative humidity      |
| rainfall_mm        | float    | Rainfall in mm         |
| population         | int      | Population             |
| population_density | float    | Population density     |

---

## 🎨 Frontend Design

### UI Technologies

* Plotly.js interactive charts
* Dark-theme dashboard
* Vanilla JavaScript state management
* Responsive analytics interface

### Theme Colors

* Background: #070d17
* Card: #0d1b2a
* Primary: #00d4ff

### Risk Palette

* Low → #2ecc71
* Moderate → #f39c12
* High → #e67e22
* Critical → #e74c3c

---

## ☁️ Deployment

The application is deployed on Render.

🔗 Live Application:
[https://epipulse-flask.onrender.com/](https://epipulse-flask.onrender.com/)

---

## 📈 Future Improvements

* Real-time health API integration
* GIS heatmap visualization
* Mobile responsive optimization
* Deep learning forecasting models
* Government healthcare dataset integration
* User authentication system
* Exportable reports & analytics

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

3. Commit your changes

```bash
git commit -m "Add your feature"
```

4. Push to GitHub

```bash
git push origin feature/your-feature
```

5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgements

* statsmodels — ARIMA implementation
* scikit-learn — Isolation Forest & MLP
* Plotly.js — Interactive charting
* Flask — Web framework

---

## 👨‍💻 Author

### Tabrej Ansari

Final Year B.Tech CSE Student
Aspiring AI & Data Analytics Enthusiast

🔗 GitHub: [https://github.com/mrmirza19k](https://github.com/mrmirza19k)

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub.
