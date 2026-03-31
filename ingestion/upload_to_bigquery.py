import os
import argparse
from pathlib import Path
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "events"

def upload_parquet_to_bigquery():
    """Reads local Parquet files created by Spark and uploads them directly to BigQuery."""
    dataset_name = os.getenv("BQ_DATASET", "github_analytics")
    table_name = "external_github_events"
    
    client = bigquery.Client()
    table_id = f"{client.project}.{dataset_name}.{table_name}"
    
    parquet_files = list(PROCESSED_DIR.rglob("*.parquet"))
    
    if not parquet_files:
        print(f"No parquet files found in {PROCESSED_DIR}")
        return

    print(f"Found {len(parquet_files)} parquet files. Uploading to BigQuery table {table_id}...")
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replace for this run
        autodetect=True
    )

    for i, file_path in enumerate(parquet_files):
        print(f"[{i+1}/{len(parquet_files)}] Uploading {file_path.name}...")
        with open(file_path, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_id, job_config=job_config)
            job.result()  # Wait for the job to complete
            
        # Switch to append after the first file
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

    # Verify
    table = client.get_table(table_id)
    print(f"\n✅ Upload complete! Table {table_id} now has {table.num_rows} rows.")

if __name__ == "__main__":
    upload_parquet_to_bigquery()
