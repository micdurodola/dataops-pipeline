from pyspark.sql import functions as F


REQUIRED_COLUMNS = [
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "transaction_date",
    "transaction_type",
]


def clean_transactions(df):
    """Validate required columns and clean transaction data."""

    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(df.columns))

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

    return (
        df
        .withColumn("transaction_id", F.trim(F.col("transaction_id")))
        .withColumn("customer_id", F.trim(F.col("customer_id")))
        .withColumn("amount", F.trim(F.col("amount")))
        .withColumn("currency", F.upper(F.trim(F.col("currency"))))
        .withColumn("transaction_date", F.trim(F.col("transaction_date")))
        .withColumn("transaction_type", F.lower(F.trim(F.col("transaction_type"))))
    )


def enrich_transactions(df, threshold=10000):
    """Add transaction date attributes and high-value classification."""

    return (
        df
        .withColumn(
            "transaction_day",
            F.date_format(F.col("transaction_date"), "yyyy-MM-dd")
        )
        .withColumn(
            "transaction_year",
            F.year(F.col("transaction_date"))
        )
        .withColumn(
            "transaction_month",
            F.month(F.col("transaction_date"))
        )
        .withColumn(
            "is_high_value",
            F.col("amount") >= F.lit(threshold)
        )
    )