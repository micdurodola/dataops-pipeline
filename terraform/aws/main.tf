# DESIGN ONLY: This configuration is validated in CI, never applied by CI.
# Use a globally unique project_name before a real deployment.
provider "aws" {
  region = var.aws_region
}

locals {
  prefix = "${var.project_name}-${var.environment}"
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket" "raw" {
  bucket = "${local.prefix}-raw"
  tags   = local.tags
}

resource "aws_s3_bucket" "processed" {
  bucket = "${local.prefix}-processed"
  tags   = local.tags
}

resource "aws_s3_bucket" "quarantine" {
  bucket = "${local.prefix}-quarantine"
  tags   = local.tags
}

resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.prefix}-artifacts"
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "all" {
  for_each = {
    raw        = aws_s3_bucket.raw.id
    processed  = aws_s3_bucket.processed.id
    quarantine = aws_s3_bucket.quarantine.id
    artifacts  = aws_s3_bucket.artifacts.id
  }
  bucket                  = each.value
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "all" {
  for_each = {
    raw        = aws_s3_bucket.raw.id
    processed  = aws_s3_bucket.processed.id
    quarantine = aws_s3_bucket.quarantine.id
    artifacts  = aws_s3_bucket.artifacts.id
  }
  bucket = each.value
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

data "aws_iam_policy_document" "glue_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue" {
  name               = "${local.prefix}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
  tags               = local.tags
}

data "aws_iam_policy_document" "glue_s3" {
  statement {
    sid = "ListDataBuckets"
    actions = ["s3:ListBucket"]
    resources = [
      aws_s3_bucket.raw.arn,
      aws_s3_bucket.processed.arn,
      aws_s3_bucket.quarantine.arn,
      aws_s3_bucket.artifacts.arn
    ]
  }
  statement {
    sid       = "ReadRawAndScripts"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.raw.arn}/*", "${aws_s3_bucket.artifacts.arn}/*"]
  }
  statement {
    sid       = "WriteProcessedAndQuarantine"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.processed.arn}/*", "${aws_s3_bucket.quarantine.arn}/*"]
  }
}

resource "aws_iam_role_policy" "glue_s3" {
  name   = "${local.prefix}-s3-access"
  role   = aws_iam_role.glue.id
  policy = data.aws_iam_policy_document.glue_s3.json
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_glue_job" "transactions" {
  name     = "${local.prefix}-transactions"
  role_arn = aws_iam_role.glue.arn

  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://${aws_s3_bucket.artifacts.bucket}/${var.glue_script_key}"
  }

  max_capacity = 0.0625
  default_arguments = {
    "--job-language" = "python"
    "--raw_bucket"   = aws_s3_bucket.raw.bucket
    "--output_bucket" = aws_s3_bucket.processed.bucket
    "--quarantine_bucket" = aws_s3_bucket.quarantine.bucket
  }
  tags = local.tags
}
# Note: Local pandas script is NOT Glue-ready. Glue deployment requires an
# AWS-aware adapter using S3 paths, dependencies and Glue job arguments.
