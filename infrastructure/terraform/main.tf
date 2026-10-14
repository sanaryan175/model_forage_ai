# ModelForge AI on AWS, sized for a $100 credit budget.
#
#   Laptop: frontend + API + TensorRT GPU worker  ──►  S3, SQS, RDS
#   AWS:    ECS Fargate CPU worker (TFLite + ONNX baseline) polls SQS
#
# Everything runs in the account's default VPC on public subnets, with security
# groups doing the isolation. Private subnets would need a NAT gateway (~$32/month)
# just so the worker can reach ECR/S3/SQS, which this budget can't justify.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = { Project = var.project }
  }
}

locals {
  name = var.project
}

data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ── S3: uploaded models + converted artifacts ───────────────────
# Layout: models/{user_id}/{model_id}/{original|converted}/...
resource "aws_s3_bucket" "models" {
  bucket        = "${local.name}-models-${data.aws_caller_identity.current.account_id}" # bucket names are global
  force_destroy = true                                                                  # lets `terraform destroy` remove it even with files inside
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket                  = aws_s3_bucket.models.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── SQS: one queue per worker type, each with a dead-letter queue ─
# The API publishes {"job_id": ...} here when a user starts a conversion.
module "cpu_queue" { # TFLite + ONNX baseline (+ Core ML, which reports "needs macOS")
  source     = "./modules/queue_with_dlq"
  queue_name = "${local.name}-cpu"
}

module "tensorrt_queue" { # consumed by the GPU worker on the laptop
  source     = "./modules/queue_with_dlq"
  queue_name = "${local.name}-tensorrt"
}

# ── RDS PostgreSQL: shared by the API (laptop) and every worker ──
resource "aws_security_group" "db" {
  name        = "${local.name}-db"
  description = "Postgres: reachable only from the laptop IP and the ECS workers"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Laptop (API + GPU worker)"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  ingress {
    description     = "ECS workers"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.workers.id]
  }
}

resource "aws_db_instance" "postgres" {
  identifier              = "${local.name}-db"
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = "db.t4g.micro" # smallest; ~$15/month
  allocated_storage       = 20
  storage_type            = "gp3"
  db_name                 = "modelforge"
  username                = "modelforge"
  password                = var.db_password
  publicly_accessible     = true # the API runs on the laptop; the security group limits who can connect
  vpc_security_group_ids  = [aws_security_group.db.id]
  backup_retention_period = 0    # student project: no paid backups
  skip_final_snapshot     = true # destroy without leaving a billable snapshot
  storage_encrypted       = true
}
