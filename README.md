Financial DataOps Pipeline

A simple financial transaction ETL pipeline built with Python and PySpark. The project processes CSV transaction data, validates records, and writes the results to Parquet.

Tech Stack

* Python 3.11
* PySpark
* Pytest
* GitHub Actions
* Python Wheel
* Terraform (AWS infrastructure design)

Dependencies

Defined in requirements.txt:

pyspark>=3.5,<4
pytest>=8,<10
build>=1.2,<2

Java 17 is required to run PySpark.

Project Structure

src/
├── main.py           # Pipeline entry point
├── reader.py         # Read CSV data
├── transactions.py   # Clean and enrich transactions
├── validation.py     # Validate records
├── daily.py          # Daily aggregation
└── writer.py         # Write output datasets
tests/                # Pytest tests
data/raw/             # Input CSV
terraform/aws/        # Proposed AWS infrastructure
.github/workflows/    # GitHub Actions CI

Pipeline

The pipeline follows these steps:

CSV → Cleaning → Validation → Enrichment → Aggregation → Parquet

Invalid transactions are written to a separate CSV quarantine folder with rejection reasons.

Output

Dataset	Location
Processed transactions	data/processed/transactions.parquet/
Daily summary	data/aggregated/daily_summary.parquet/
Rejected transactions	data/quarantine/rejected_transactions/

Pipeline logs are saved to logs/pipeline.log.

Running the Pipeline

python -m src.main

Testing

The project includes PySpark tests for validation, missing columns, aggregation, high-value transactions, and end-to-end processing.

python -m pytest tests/ -v

Python Wheel

The ETL code is packaged as a Python wheel using pyproject.toml.

python -m build --wheel

The generated wheel is stored in dist/.

GitHub Actions

The CI workflow runs automatically on pushes and pull requests.

It performs three main tasks:

1. Runs the Python tests.
2. Builds the Python wheel if the tests pass.
3. Uploads the wheel as a GitHub Actions artifact.

AWS

The terraform/aws/ directory contains a proposed AWS infrastructure setup using S3, Glue, and IAM.

The plan is to upload the Python wheel to S3 and use it as a dependency in an AWS Glue job.

AWS deployment is not implemented in this prototype.