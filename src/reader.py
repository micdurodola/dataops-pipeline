from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
)

TRANSACTION_SCHEMA = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("amount", StringType(), True),
    StructField("currency", StringType(), True),
    StructField("transaction_date", StringType(), True),
    StructField("transaction_type", StringType(), True),
])


def read_transactions(spark: SparkSession, path: str):
    return (
        spark.read
        .option("header", True)
        .option("mode", "FAILFAST")
        .schema(TRANSACTION_SCHEMA)
        .csv(path)
    )