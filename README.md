# 🔭 GitHub Open Source Activity Tracker

An end-to-end data engineering pipeline that ingests, processes, and visualizes GitHub public event data from [GH Archive](https://www.gharchive.org/). Built as the capstone project for the [Data Engineering Zoomcamp 2026](https://github.com/DataTalksClub/data-engineering-zoomcamp).

## 📊 Dashboard Preview

> _Screenshots will be added after the dashboard is complete._

## 🏗️ Architecture

```
GH Archive (JSON.gz, hourly)
        │
        ▼
┌─────────────────┐
│  Ingestion       │  Python scripts (download + upload)
│  (Kestra DAG)    │  Orchestrated with Kestra
└────────┬────────┘
         ▼
┌─────────────────┐
│  Google Cloud    │  Raw JSON.gz files
│  Storage (Lake)  │  gs://gh-archive-data-lake/raw/
└────────┬────────┘
         ▼
┌─────────────────┐
│  PySpark Batch   │  Parse, flatten, clean events
│  Processing      │  Output: Partitioned Parquet
└────────┬────────┘
         ▼
┌─────────────────┐
│  BigQuery (DWH)  │  Partitioned by date
│                  │  Clustered by event_type, repo
└────────┬────────┘
         ▼
┌─────────────────┐
│  dbt             │  Staging + mart models
│  Transformations │  Tests & documentation
└────────┬────────┘
         ▼
┌─────────────────┐
│  Streamlit       │  2+ interactive tiles
│  Dashboard       │  Event trends & distribution
└─────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Infrastructure** | Terraform (IaC) |
| **Cloud** | Google Cloud Platform |
| **Data Lake** | Google Cloud Storage |
| **Orchestration** | Kestra |
| **Batch Processing** | PySpark |
| **Data Warehouse** | BigQuery |
| **Transformations** | dbt |
| **Dashboard** | Streamlit + Plotly |

## 📁 Project Structure

```
├── terraform/              # IaC for GCP resources
├── flows/                  # Kestra orchestration flows
├── ingestion/              # Data ingestion scripts
├── spark/                  # PySpark batch processing
├── dbt/github_analytics/   # dbt models & tests
├── dashboard/              # Streamlit dashboard app
├── Makefile                # Common commands
├── requirements.txt        # Python dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Java 17 (for PySpark)
- Terraform
- GCP account with free tier credits
- GCP service account key (JSON)

### 1. Clone & Install

```bash
git clone https://github.com/barshal-horse/github-activity-tracker.git
cd github-activity-tracker
pip install -r requirements.txt
```

### 2. Set Up Infrastructure

```bash
# Create a .env file with your GCP config
cp .env.example .env
# Edit .env with your GCP project ID

# Initialize and apply Terraform
make terraform-init
make terraform-apply
```

### 3. Ingest Data

```bash
# Download & upload 1 week of GH Archive data
make ingest START_DATE=2026-02-17 END_DATE=2026-02-23
```

### 4. Process with Spark

```bash
make spark START_DATE=2026-02-17 END_DATE=2026-02-23
```

### 5. Run dbt Transformations

```bash
make dbt-run
make dbt-test
```

### 6. Launch Dashboard

```bash
make dashboard
# Opens at http://localhost:8501
```

### One-Command Pipeline

```bash
make pipeline START_DATE=2026-02-17 END_DATE=2026-02-23
```

## 📈 Dashboard Tiles

1. **Event Type Distribution** — Bar chart showing the breakdown of GitHub event types (Push, Watch, Fork, PR, Issues, etc.)
2. **Daily Activity Trends** — Line chart showing event volume over time, colored by event type

## 📊 Data Source

- **[GH Archive](https://www.gharchive.org/)** — Records the entire public GitHub timeline as hourly JSON archives
- **Scope:** 1 week of data (168 hourly files, ~2-3 GB raw)
- **Event Types:** PushEvent, WatchEvent, ForkEvent, PullRequestEvent, IssuesEvent, and more

## 🙏 Acknowledgments

- [DataTalksClub](https://github.com/DataTalksClub) for the Data Engineering Zoomcamp
- [GH Archive](https://www.gharchive.org/) by Ilya Grigorik
