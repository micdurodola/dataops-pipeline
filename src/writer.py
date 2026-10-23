def write_parquet(df, path):
    (
        df.write
        .mode("overwrite")
        .parquet(path)
    )


def write_quarantine(df, path):
    (
        df.write
        .mode("overwrite")
        .option("header", True)
        .csv(path)
    )