variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "project_name" {
  type    = string
  default = "financial-dataops-demo"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "glue_script_key" {
  type    = string
  default = "scripts/v1.0.0/pipeline.py"
}
