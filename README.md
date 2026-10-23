# Financial DataOps — PySpark Local Prototype

**Implemented:** Local CSV → PySpark validation/transformations → Parquet datasets + CSV quarantine; Pytest, GitHub Actions, JSON run audit. **No Pandas, no PyArrow package requirement, no AWS deployment, no Docker.** Spark uses its own JVM-backed Parquet support.

## MacBook / VS Code setup

Install Java 17 (`brew install --cask temurin@17`), then check `java -version` and `echo $JAVA_HOME`. PySpark 3.5 supports Java 8/11/17; Java 17 is the recommended choice for this project. Use Python 3.11 or 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -v
python -m src.pipeline
```

If Spark cannot find Java on macOS, try `export JAVA_HOME=$(/usr/libexec/java_home -v 17)` in your terminal before running it.

## Outputs

- `data/processed/transactions.parquet/` — **directory** of Spark-generated Parquet part files
- `data/aggregated/daily_summary.parquet/` — daily counts and amounts **grouped by currency**
- `data/quarantine/rejected_transactions/` — CSV part files containing rejected rows and reasons
- `runs/<timestamp>.json` — input SHA-256, record counts, duration, code version

Spark writes directories, not individual `.parquet` files. It is expected to see `part-00000-....parquet` inside each output folder.

## Inspect output using PySpark

```bash
python
```
```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.master('local[2]').appName('inspect').getOrCreate()
df = spark.read.parquet('data/processed/transactions.parquet')
df.groupBy('currency').sum('amount').show()
spark.stop()
```

## Rules

Required fields, positive amounts, ISO date, supported currencies (GBP/USD/EUR), supported transaction types, and transaction ID uniqueness. **All rows sharing a duplicate ID are quarantined**, avoiding nondeterministic deduplication. Accepted + rejected = total. High-value flag is a demo enrichment, not fraud detection. Decimal(18,2) avoids binary floating-point currency sums. The example assumes positive transaction amounts and uses transaction type to describe direction.

**Reruns overwrite** the same output folders. This avoids accumulating duplicate data, but is not a production-grade atomic multi-dataset commit. Data is synthetic. Spark reads the CSV with an explicit schema and fails on malformed records.

## CI and IaC

GitHub Actions runs Pytest, executes the local Spark ETL on a hosted runner, checks Parquet outputs, and uploads output artifacts. A separate job validates `terraform/aws/` without deploying AWS resources. Terraform describes an **illustrative** S3/Glue/IAM production design; the local pipeline does not yet read/write S3 and is not a deployable Glue script. Terraform validation is not infrastructure provisioning.

The example does not require secrets. Configuration comes from process environment variables; `.env.example` is documentation only, not automatically loaded.

## Suggested interview demo

Show CSV, run tests, run ETL, show logs/audit JSON, inspect Parquet with Spark, show quarantined records, show GitHub Actions run, and explain Glue/S3 as a production extension.
