from pyspark.sql import functions as F


def aggregate_daily(df):
    return (
        df
        .groupBy("transaction_day", "currency")
        .agg(
            F.count("*").alias("transaction_count"),
            F.sum("amount").alias("total_amount")
        )
    )