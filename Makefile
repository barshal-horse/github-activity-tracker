.PHONY: setup terraform-init terraform-apply ingest spark dbt dashboard clean

# ============================================================
# Setup
# ============================================================
setup:
	pip install -r requirements.txt

# ============================================================
# Terraform
# ============================================================
terraform-init:
	cd terraform && terraform init

terraform-plan:
	cd terraform && terraform plan

terraform-apply:
	cd terraform && terraform apply -auto-approve

terraform-destroy:
	cd terraform && terraform destroy -auto-approve

# ============================================================
# Data Ingestion
# ============================================================
ingest:
	python ingestion/download_gharchive.py --start-date $(START_DATE) --end-date $(END_DATE)
	python ingestion/upload_to_gcs.py --start-date $(START_DATE) --end-date $(END_DATE)

ingest-local:
	python ingestion/download_gharchive.py --start-date $(START_DATE) --end-date $(END_DATE)

# ============================================================
# Spark Processing
# ============================================================
spark:
	python spark/process_events.py --start-date $(START_DATE) --end-date $(END_DATE)

# ============================================================
# dbt
# ============================================================
dbt-run:
	cd dbt/github_analytics && dbt run

dbt-test:
	cd dbt/github_analytics && dbt test

dbt-docs:
	cd dbt/github_analytics && dbt docs generate && dbt docs serve

# ============================================================
# Dashboard
# ============================================================
dashboard:
	streamlit run dashboard/app.py

# ============================================================
# Full Pipeline
# ============================================================
pipeline: ingest spark dbt-run
	@echo "Pipeline complete!"

# ============================================================
# Cleanup
# ============================================================
clean:
	rm -rf data/raw data/processed spark-warehouse metastore_db derby.log
