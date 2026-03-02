"""
Upload raw GH Archive files from local disk to Google Cloud Storage.

Usage:
    python upload_to_gcs.py --start-date 2026-02-17 --end-date 2026-02-23

Uploads from: data/raw/gharchive/{date}/{file}.json.gz
Uploads to:   gs://{bucket}/raw/gharchive/{date}/{file}.json.gz
"""

import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gharchive"


def upload_to_gcs(bucket_name: str, start_date: str, end_date: str):
    """Upload all raw GH Archive files to GCS."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    print(f"☁️  Uploading to GCS bucket: {bucket_name}")
    print(f"   Date range: {start_date} → {end_date}")

    uploaded = 0
    current = start

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        day_dir = RAW_DIR / date_str

        if not day_dir.exists():
            print(f"  ⚠ Skipping {date_str} — no local files found")
            current += timedelta(days=1)
            continue

        print(f"\n📅 Uploading {date_str}...")

        for file_path in sorted(day_dir.glob("*.json.gz")):
            gcs_path = f"raw/gharchive/{date_str}/{file_path.name}"
            blob = bucket.blob(gcs_path)

            if blob.exists():
                print(f"  ✓ Already uploaded: {file_path.name}")
            else:
                blob.upload_from_filename(str(file_path))
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  ✓ Uploaded: {file_path.name} ({size_mb:.1f} MB)")

            uploaded += 1

        current += timedelta(days=1)

    print(f"\n✅ Uploaded {uploaded} files to gs://{bucket_name}/raw/gharchive/")


def main():
    parser = argparse.ArgumentParser(description="Upload GH Archive data to GCS")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date inclusive (YYYY-MM-DD)")
    parser.add_argument(
        "--bucket", default=os.getenv("GCS_BUCKET", "gh-archive-data-lake"),
        help="GCS bucket name"
    )
    args = parser.parse_args()

    upload_to_gcs(args.bucket, args.start_date, args.end_date)


if __name__ == "__main__":
    main()
