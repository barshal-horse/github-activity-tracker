"""
PySpark batch job to process raw GH Archive JSON data.

Reads raw JSON.gz → flattens nested fields → writes partitioned Parquet.

Usage:
    python process_events.py --start-date 2026-02-17 --end-date 2026-02-23
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Set up Java and Hadoop for Windows
if sys.platform == "win32":
    if not os.environ.get("JAVA_HOME"):
        java_dir = r"C:\Program Files\Microsoft\jdk-17.0.18.8-hotspot"
        if os.path.exists(java_dir):
            os.environ["JAVA_HOME"] = java_dir
    if not os.environ.get("HADOOP_HOME"):
        hadoop_dir = r"C:\hadoop"
        if os.path.exists(hadoop_dir):
            os.environ["HADOOP_HOME"] = hadoop_dir
    os.environ["PATH"] = (
        os.environ.get("JAVA_HOME", "") + r"\bin;" +
        os.environ.get("HADOOP_HOME", "") + r"\bin;" +
        os.environ["PATH"]
    )

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_date, date_format, hour,
    from_json, get_json_object,
    coalesce, lit, when
)
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    BooleanType, TimestampType
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "gharchive"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "events"


def create_spark_session() -> SparkSession:
    """Create a local Spark session."""
    return (
        SparkSession.builder
        .master("local[*]")
        .appName("GH Archive Processor")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )


def get_input_paths(start_date: str, end_date: str) -> list:
    """Get all JSON.gz file paths for the date range."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    paths = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        day_dir = RAW_DIR / date_str
        if day_dir.exists():
            paths.extend([str(f) for f in sorted(day_dir.glob("*.json.gz"))])
        current += timedelta(days=1)

    return paths


def process_events(spark: SparkSession, input_paths: list, output_path: str):
    """Read raw JSON, flatten, and write partitioned Parquet."""

    print(f"📖 Reading {len(input_paths)} JSON files...")
    df_raw = spark.read.json(input_paths)

    print(f"   Total raw records: {df_raw.count()}")
    print(f"   Schema:")
    df_raw.printSchema()

    # Flatten and select key fields
    df_processed = df_raw.select(
        col("id").alias("event_id"),
        col("type").alias("event_type"),
        col("public"),
        col("created_at").cast(TimestampType()).alias("created_at"),
        to_date(col("created_at")).alias("event_date"),
        hour(col("created_at").cast(TimestampType())).alias("event_hour"),

        # Actor (user who triggered the event)
        col("actor.id").alias("actor_id"),
        col("actor.login").alias("actor_login"),
        col("actor.display_login").alias("actor_display_login"),

        # Repository
        col("repo.id").alias("repo_id"),
        col("repo.name").alias("repo_name"),

        # Organization (if present)
        col("org.id").alias("org_id"),
        col("org.login").alias("org_login"),
    )

    # Repartition by event_date for efficient downstream queries
    num_dates = df_processed.select("event_date").distinct().count()
    num_partitions = max(num_dates * 2, 4)  # ~2 partitions per day

    print(f"\n📝 Writing {df_processed.count()} processed records...")
    print(f"   Output: {output_path}")
    print(f"   Partitions: {num_partitions} (by event_date)")

    (
        df_processed
        .repartition(num_partitions, "event_date")
        .write
        .mode("overwrite")
        .partitionBy("event_date")
        .parquet(output_path)
    )

    print("✅ Processing complete!")

    # Show summary stats
    print("\n📊 Summary:")
    df_processed.groupBy("event_type").count().orderBy(col("count").desc()).show(20)
    df_processed.groupBy("event_date").count().orderBy("event_date").show(10)


def main():
    parser = argparse.ArgumentParser(description="Process GH Archive data with Spark")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date inclusive (YYYY-MM-DD)")
    parser.add_argument("--output", default=str(PROCESSED_DIR), help="Output directory")
    args = parser.parse_args()

    print("⚡ GH Archive Spark Processor")
    print(f"   Date range: {args.start_date} → {args.end_date}")

    input_paths = get_input_paths(args.start_date, args.end_date)
    if not input_paths:
        print("❌ No input files found! Run the ingestion step first.")
        sys.exit(1)

    print(f"   Input files: {len(input_paths)}")

    spark = create_spark_session()
    print(f"   Spark version: {spark.version}")

    try:
        process_events(spark, input_paths, args.output)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
