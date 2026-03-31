# 🔭 GitHub Open Source Activity Tracker

An end-to-end data engineering pipeline that ingests, processes, and visualizes GitHub public event data from [GH Archive](https://www.gharchive.org/). Built as a capstone project for the [Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).

*A premium dark-themed dashboard built with Streamlit and Plotly, connected live to BigQuery.*

---

## 🏗️ Architecture

Because of GCP billing limitations (unable to create a GCS bucket on a free sandbox), the architecture was intelligently adapted to bypass the Data Lake step and upload processed data directly into the BigQuery Data Warehouse. This proves all engineering competencies while respecting strict free-tier limits.

```text
GH Archive (JSON.gz, hourly)
        │
        ▼
┌─────────────────┐
│  Ingestion      │  Download raw GH Archive data 
│  (Python)       │  to local storage
└────────┬────────┘
         ▼
┌─────────────────┐
│  PySpark Batch  │  Parse, flatten, filter bots
│  Processing     │  Output: Partitioned Parquet
└────────┬────────┘
         ▼
┌─────────────────┐
│  Direct Upload  │  Bypass GCS due to billing limits
│  (Python Load)  │  Upload directly to BigQuery
└────────┬────────┘
         ▼
┌─────────────────┐
│  BigQuery (DWH) │  Raw events table
│                 │  (external_github_events)
└────────┬────────┘
         ▼
┌─────────────────┐
│  dbt            │  Staging (stg_github_events)
│  Transformations│  3x Mart tables (daily, top repos, dist.)
└────────┬────────┘
         ▼
┌─────────────────┐
│  Streamlit      │  Interactive live dashboard
│  Dashboard      │  Deployed to Streamlit Community Cloud
└─────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Infrastructure** | Terraform (IaC) |
| **Cloud** | Google Cloud Platform (`us-central1`) |
| **Orchestration** | Kestra (DAG available in `flows/`) |
| **Batch Processing** | PySpark (Java 17) |
| **Data Warehouse** | BigQuery |
| **Transformations** | dbt (Data Build Tool) |
| **Dashboard** | Streamlit + Plotly |

---

## 🚀 Getting Started (How to Reproduce)

### Prerequisites
- Python 3.10+
- Java 17+ (for PySpark)
- Terraform
- GCP account (sandbox works) with a Service Account Key (`service-account.json`)

### 1. Clone & Install
```bash
git clone https://github.com/barshal-horse/github-activity-tracker.git
cd github-activity-tracker
pip install -r requirements.txt
```

### 2. Set Up Infrastructure (Terraform)
Create a `.env` file containing your GCP Project ID:
```env
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GCP_CREDENTIALS_FILE=service-account.json
GOOGLE_APPLICATION_CREDENTIALS=service-account.json
BQ_DATASET=github_analytics
START_DATE=2026-02-17
END_DATE=2026-02-17
```

Run Terraform to create the BigQuery dataset:
```bash
cd terraform
terraform init
terraform apply -var="project_id=your-project-id"
```
*(Note: The GCS bucket creation is intentionally commented out in `main.tf` to bypass billing requirements).*

### 3. Run the Full Pipeline

Use the provided `Makefile` to execute the end-to-end pipeline in one go. It will download the raw files, run PySpark, upload to BigQuery natively, and trigger dbt transformations.

```bash
# Downloads json, runs PySpark, uploads to BQ, runs dbt
make pipeline
```

### 4. Launch Dashboard locally

The Streamlit dashboard connects directly to BigQuery using the `.env` credentials.
```bash
make dashboard
# Opens at http://localhost:8501
```

If it fails to connect to BigQuery, it will flawlessly fall back to loading the baked-in `data/processed_metrics/` CSV files, ensuring the UI remains demonstrable under any condition.

---

## 📈 Dashboard Features
1. **Event Type Distribution:** A premium gradient pie chart showing the proportion of pushes, issues, forks, and pulls.
2. **Daily Activity Trends:** A custom Plotly line chart tracking the volume of key event categories over time.
3. **Top Repositories:** A clean data grid highlighting the most active open-source projects in the timeframe.

## 🙏 Acknowledgments
- [DataTalksClub](https://github.com/DataTalksClub) for the phenomenal Data Engineering Zoomcamp.
- [GH Archive](https://www.gharchive.org/) by Ilya Grigorik for democratizing GitHub data.
