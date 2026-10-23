provider "aws" {
  region = var.aws_region
}

# S3 bucket
resource "aws_s3_bucket" "dataops" {
  bucket = var.bucket_name
}

# Block public access
resource "aws_s3_bucket_public_access_block" "dataops" {
  bucket = aws_s3_bucket.dataops.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM role for AWS Glue
resource "aws_iam_role" "glue_role" {
  name = "financial-dataops-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# AWS Glue service permissions
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# S3 permissions for Glue
resource "aws_iam_role_policy" "glue_s3" {
  name = "financial-dataops-s3-access"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.dataops.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.dataops.arn}/*"
      }
    ]
  })
}

# AWS Glue job
resource "aws_glue_job" "financial_etl" {
  name     = "financial-dataops-etl"
  role_arn = aws_iam_role.glue_role.arn

  glue_version = "5.0"

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${aws_s3_bucket.dataops.bucket}/scripts/glue_job.py"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--additional-python-modules"        = "s3://${aws_s3_bucket.dataops.bucket}/wheels/financial_dataops_pyspark-0.1.0-py3-none-any.whl"
    "--enable-job-insights"              = "true"
    "--enable-continuous-cloudwatch-log" = "true"
  }

  worker_type       = "G.1X"
  number_of_workers = 2
}