output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.dataops.bucket
}

output "glue_job_name" {
  description = "AWS Glue job name"
  value       = aws_glue_job.financial_etl.name
}

output "glue_role_arn" {
  description = "IAM role used by AWS Glue"
  value       = aws_iam_role.glue_role.arn
}