from pyspark.sql import functions as F
from pyspark.sql.window import Window


def validate_transactions(df):

    duplicate_window = Window.partitionBy("transaction_id")

    df = (
        df
        .withColumn(
            "amount_decimal",
            F.expr("try_cast(amount AS DECIMAL(18,2))")
        )
        .withColumn(
            "date_parsed",
            F.expr("try_cast(transaction_date AS DATE)")
        )
        .withColumn(
            "duplicate_count",
            F.count("*").over(duplicate_window)
        )
    )

    df = df.withColumn(
        "rejection_reason",
        F.concat_ws(
            ";",
            F.when(
                F.col("transaction_id").isNull()
                | (F.col("transaction_id") == ""),
                "missing_transaction_id"
            ),
            F.when(
                F.col("customer_id").isNull()
                | (F.col("customer_id") == ""),
                "missing_customer_id"
            ),
            F.when(
                F.col("duplicate_count") > 1,
                "duplicate_transaction_id"
            ),
            F.when(
                F.col("amount_decimal").isNull()
                | (F.col("amount_decimal") <= 0),
                "invalid_amount"
            ),
            F.when(
                F.col("date_parsed").isNull()
                | (
                    F.date_format("date_parsed", "yyyy-MM-dd")
                    != F.col("transaction_date")
                ),
                "invalid_date"
            ),
            F.when(
                ~F.coalesce(
                    F.col("currency").isin("GBP", "USD", "EUR"),
                    F.lit(False)
                ),
                "unsupported_currency"
            ),
            F.when(
                ~F.coalesce(
                    F.col("transaction_type").isin(
                        "deposit",
                        "withdrawal",
                        "transfer",
                        "payment",
                        "refund"
                    ),
                    F.lit(False)
                ),
                "unsupported_transaction_type"
            )
        )
    )

    valid = (
        df
        .filter(F.col("rejection_reason") == "")
        .drop(
            "amount",
            "transaction_date",
            "duplicate_count",
            "rejection_reason"
        )
        .withColumnRenamed("amount_decimal", "amount")
        .withColumnRenamed("date_parsed", "transaction_date")
    )

    invalid = (
        df
        .filter(F.col("rejection_reason") != "")
    )

    return valid, invalid