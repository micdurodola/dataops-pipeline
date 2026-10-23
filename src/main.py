import logging
import time
from pathlib import Path

from pyspark.sql import SparkSession

from src.reader import read_transactions
from src.transactions import clean_transactions, enrich_transactions
from src.validation import validate_transactions
from src.daily import aggregate_daily
from src.writer import write_parquet, write_quarantine


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("FinancialDataOps")

# Create logs directory
Path("logs").mkdir(exist_ok=True)

# Configure file logging
file_handler = logging.FileHandler("logs/pipeline.log")

file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
)

logger.addHandler(file_handler)


def run_pipeline():

    start_time = time.time()

    logger.info("Starting Financial DataOps ETL pipeline")

    spark = None
    valid_df = None
    invalid_df = None

    try:
        spark = (
            SparkSession.builder
            .appName("Financial-DataOps-ETL")
            .master("local[2]")
            .getOrCreate()
        )

        spark.sparkContext.setLogLevel("ERROR")

        # Extract
        logger.info("Reading financial transactions")

        raw_df = read_transactions(
            spark,
            "data/raw/transactions.csv"
        )

        total_count = raw_df.count()
        logger.info("Total transactions ingested: %s", total_count)

        # Transform
        logger.info("Cleaning transaction data")
        cleaned_df = clean_transactions(raw_df)

        # Validate
        logger.info("Validating transactions")
        valid_df, invalid_df = validate_transactions(cleaned_df)

        valid_df = valid_df.cache()
        invalid_df = invalid_df.cache()

        valid_count = valid_df.count()
        invalid_count = invalid_df.count()

        logger.info("Valid transactions: %s", valid_count)
        logger.warning("Rejected transactions: %s", invalid_count)

        # Data reconciliation
        if total_count != valid_count + invalid_count:
            raise ValueError("Data reconciliation failed")

        logger.info("Data reconciliation passed")

        # Enrich
        logger.info("Enriching valid transactions")
        enriched_df = enrich_transactions(valid_df)

        # Aggregate
        logger.info("Aggregating daily transactions")
        daily_df = aggregate_daily(enriched_df)

        # Load
        logger.info("Writing processed transactions")
        write_parquet(
            enriched_df,
            "data/processed/transactions.parquet"
        )

        logger.info("Writing daily aggregation")
        write_parquet(
            daily_df,
            "data/aggregated/daily_summary.parquet"
        )

        logger.info("Writing rejected transactions")
        write_quarantine(
            invalid_df,
            "data/quarantine/rejected_transactions"
        )

        duration = round(time.time() - start_time, 2)

        logger.info("ETL pipeline completed successfully")
        logger.info("Execution time: %s seconds", duration)

    except Exception:
        logger.exception("ETL pipeline failed")
        raise

    finally:
        if valid_df is not None:
            valid_df.unpersist()

        if invalid_df is not None:
            invalid_df.unpersist()

        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    run_pipeline()