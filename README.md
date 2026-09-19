# ☁️ Cloud Demand Forecasting & Capacity Optimization System

[![Live Dashboard](https://img.shields.io/badge/Streamlit-Live%20Demo-ff4b4b?logo=streamlit)](https://supply-demand-forecasting-and-capacity-optimization-g9mkjxqk3j.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-orange)](https://xgboost.readthedocs.io)

An enterprise-grade, end-to-end Machine Learning system for predicting cloud infrastructure resource demand (CPU, Memory, Storage) and optimizing capacity allocations across global cloud regions.

---

## 🚀 Key Features & Architecture

- **🧠 Machine Learning Pipeline**: XGBoost Regressor trained on enriched multi-region cloud usage logs with automated feature encoding and model artifact serialization (`models/xgb_model.pkl`).
- **📊 Interactive Streamlit Dashboard**: Sleek dark-themed analytics console featuring:
  - 🏠 **Executive Overview**: High-level KPIs, capacity efficiency metrics, and active alert counters.
  - 📈 **Demand Forecast**: Actual vs. XGBoost predicted demand comparison over configurable time horizons.
  - 🌍 **Regional Analysis**: Geographic workload density heatmap and risk distribution by region.
  - 🚨 **Risk & Incident Center**: Searchable grid of high-risk capacity events with automated alert tagging and CSV export.
  - 💰 **Cost Optimization**: Financial wastage tracking and capacity utilization efficiency breakdown.
  - 🔮 **What-If Scenario Simulator**: Dynamic sliders for simulating load spikes (+/- 50%) and infrastructure provisioning responses.
  - 🧠 **Model Intelligence & Drift**: Real-time evaluation of MAE/RMSE metrics, feature importance, and model drift.
  - 📊 **Data Explorer**: Paginated data inspector with global multi-column search.
- **⚡ Real-Time REST API**: FastAPI server hosting `/predict` and `/health` endpoints for low-latency scoring.
- **🔄 Automated Batch Scorer**: Scheduled pipeline step for bulk evaluation of inbound telemetry batches.

---

## 📁 Repository Structure

```text
demandcapacity/
├── api/                     # FastAPI web application endpoints & schemas
│   └── app.py               # REST API implementation
├── dashboard/               # Streamlit multi-page dashboard
│   ├── streamlit_app.py     # Main application entry point & router
│   ├── components/          # Modular UI components & page modules
│   │   ├── overview.py
│   │   ├── forecast.py
│   │   ├── regional.py
│   │   ├── risk.py
│   │   ├── cost.py
│   │   ├── whatif.py
│   │   ├── model_intelligence.py
│   │   └── data_explorer.py
│   └── utils/               # Styling, data processing & data loader helpers
├── data/                    # Telemetry & batch prediction files
├── models/                  # Saved ML models & feature metadata
├── pipeline/                # Model training & batch scoring scripts
│   ├── train_and_save.py    # Training script
│   └── batch_predict.py     # Batch scoring script
├── Dockerfile               # Container build configuration
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

---

## 💻 Local Setup & Installation

### 1. Clone & Setup Environment

Ensure Python 3.10 or higher is installed.

```bash
git clone https://github.com/mickeygems/supply-demand-forecasting-and-capacity-optimization.git
cd supply-demand-forecasting-and-capacity-optimization

# Create and activate virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 2. Train the Model & Run Pipeline

Generate model artifacts from training data:

```bash
python pipeline/train_and_save.py
```

Run batch predictions over sample incoming data:

```bash
# Set PYTHONPATH to root directory
# Windows PowerShell:
$env:PYTHONPATH="."
# Linux/macOS:
export PYTHONPATH="."

python pipeline/batch_predict.py
```

---

### 3. Launch the Streamlit Dashboard

Run the dark-themed interactive dashboard locally:

```bash
$env:PYTHONPATH="."
streamlit run dashboard/streamlit_app.py
```

Open your browser at [http://localhost:8501](http://localhost:8501).

---

### 4. Launch FastAPI REST Service

Start the FastAPI application for real-time model inference:

```bash
$env:PYTHONPATH="."
uvicorn api.app:app --reload --port 8000
```

- **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Running with Docker

You can containerize and run the complete application stack:

```bash
# Build Docker image
docker build -t demand-capacity-app .

# Run container exposing API (8000) and Dashboard (8501)
docker run -p 8000:8000 -p 8501:8501 demand-capacity-app
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
