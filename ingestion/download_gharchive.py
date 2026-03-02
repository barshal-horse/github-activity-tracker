"""
Download GH Archive hourly JSON files for a given date range.

Usage:
    python download_gharchive.py --start-date 2026-02-17 --end-date 2026-02-23

Downloads files like: https://data.gharchive.org/2026-02-17-0.json.gz
Saves to: data/raw/gharchive/2026-02-17/2026-02-17-0.json.gz
"""

import os
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm


BASE_URL = "https://data.gharchive.org"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gharchive"


def download_file(url: str, dest: Path) -> bool:
    """Download a single file from URL to destination."""
    if dest.exists():
        print(f"  ✓ Already exists: {dest.name}")
        return True

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"  ✓ Downloaded: {dest.name} ({size_mb:.1f} MB)")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Failed: {dest.name} — {e}")
        return False


def download_day(date: datetime) -> int:
    """Download all 24 hourly archives for a single day."""
    date_str = date.strftime("%Y-%m-%d")
    day_dir = RAW_DIR / date_str
    day_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📅 Downloading {date_str} (24 hourly files)...")

    success_count = 0
    for hour in range(24):
        filename = f"{date_str}-{hour}.json.gz"
        url = f"{BASE_URL}/{filename}"
        dest = day_dir / filename

        if download_file(url, dest):
            success_count += 1

    return success_count


def main():
    parser = argparse.ArgumentParser(description="Download GH Archive data")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date inclusive (YYYY-MM-DD)")
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    print(f"🔭 GH Archive Downloader")
    print(f"   Date range: {args.start_date} → {args.end_date}")
    print(f"   Output dir: {RAW_DIR}")

    total_files = 0
    current = start
    while current <= end:
        total_files += download_day(current)
        current += timedelta(days=1)

    days = (end - start).days + 1
    print(f"\n✅ Done! Downloaded {total_files}/{days * 24} files")
    print(f"   Location: {RAW_DIR}")


if __name__ == "__main__":
    main()
