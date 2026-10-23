import csv

import pytest
from pyspark.sql import SparkSession

from src.reader import read_transactions
from src.transactions import clean_transactions, enrich_transactions
from src.validation import validate_transactions
from src.daily import aggregate_daily
from src.writer import write_parquet, write_quarantine


HEADERS = [
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "transaction_date",
    "transaction_type",
]

ROWS = [
    ("T1", "C1", "100", "gbp", "2026-09-01", "Deposit"),
    ("T2", "C1", "12000", "USD", "2026-09-02", "transfer"),
    ("T3", "C2", "-10", "EUR", "2026-09-02", "payment"),
    ("T4", "C2", "40", "XYZ", "bad-date", "transfer"),
    ("T5", "C3", "10", "GBP", "2026-09-02", "refund"),
    ("T5", "C3", "10", "GBP", "2026-09-02", "refund"),
]


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("Financial-DataOps-Tests")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )

    session.sparkContext.setLogLevel("ERROR")

    yield session

    session.stop()


def test_validation(spark):
    """Check valid and rejected transactions."""

    raw_df = spark.createDataFrame(ROWS, HEADERS)

    cleaned_df = clean_transactions(raw_df)

    valid_df, invalid_df = validate_transactions(cleaned_df)

    assert valid_df.count() == 2
    assert invalid_df.count() == 4

    duplicate_count = invalid_df.filter(
        "rejection_reason LIKE '%duplicate_transaction_id%'"
    ).count()

    assert duplicate_count == 2


def test_missing_schema(spark):
    """Check that missing required columns raise an error."""

    raw_df = spark.createDataFrame(
        [("T1",)],
        ["transaction_id"]
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        cleaned_df = clean_transactions(raw_df)
        validate_transactions(cleaned_df)


def test_aggregation_by_currency(spark):
    """Check daily aggregation keeps currencies separate."""

    raw_df = spark.createDataFrame(ROWS, HEADERS)

    cleaned_df = clean_transactions(raw_df)

    valid_df, _ = validate_transactions(cleaned_df)

    enriched_df = enrich_transactions(valid_df)

    daily_df = aggregate_daily(enriched_df)

    assert daily_df.count() == 2

    currencies = {
        row["currency"]
        for row in daily_df.collect()
    }

    assert currencies == {"GBP", "USD"}


def test_high_value_transactions(spark):
    """Check high-value transaction classification."""

    raw_df = spark.createDataFrame(ROWS, HEADERS)

    cleaned_df = clean_transactions(raw_df)

    valid_df, _ = validate_transactions(cleaned_df)

    enriched_df = enrich_transactions(valid_df)

    high_value_count = enriched_df.filter(
        "is_high_value = true"
    ).count()

    assert high_value_count == 1


def test_end_to_end(spark, tmp_path):
    """Test ingestion, transformation, validation and output."""

    input_path = tmp_path / "transactions.csv"

    with input_path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(HEADERS)
        writer.writerows(ROWS)

    # Extract
    raw_df = read_transactions(spark, str(input_path))

    # Transform
    cleaned_df = clean_transactions(raw_df)

    # Validate
    valid_df, invalid_df = validate_transactions(cleaned_df)

    # Enrich
    enriched_df = enrich_transactions(valid_df)

    # Aggregate
    daily_df = aggregate_daily(enriched_df)

    # Write outputs
    processed_path = tmp_path / "processed"
    aggregated_path = tmp_path / "aggregated"
    quarantine_path = tmp_path / "quarantine"

    write_parquet(enriched_df, str(processed_path))
    write_parquet(daily_df, str(aggregated_path))
    write_quarantine(invalid_df, str(quarantine_path))

    # Verify output directories
    assert list(processed_path.glob("part-*.parquet"))
    assert list(aggregated_path.glob("part-*.parquet"))
    assert list(quarantine_path.glob("part-*.csv"))

    # Verify processed records
    processed_df = spark.read.parquet(str(processed_path))

    assert processed_df.count() == 2

    # Verify rejected records
    rejected_df = (
        spark.read
        .option("header", True)
        .csv(str(quarantine_path))
    )

    assert rejected_df.count() == 4

    # Verify reconciliation
    assert processed_df.count() + rejected_df.count() == 6