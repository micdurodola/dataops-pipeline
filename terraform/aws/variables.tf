variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "bucket_name" {
  description = "S3 bucket for the financial DataOps pipeline"
  type        = string
  default     = "financial-dataops-yourname-2026"
}