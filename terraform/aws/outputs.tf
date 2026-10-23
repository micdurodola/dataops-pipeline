output "raw_bucket_name" {
  value = aws_s3_bucket.raw.bucket
}

output "glue_job_name" {
  value = aws_glue_job.transactions.name
}
