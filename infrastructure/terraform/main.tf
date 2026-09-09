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
  region = var.aws_region
}

locals {
  name = "${var.project}-${var.environment}"
}

# ── S3: model + artifact storage ───────────────────────────────
# Layout: models/{user_id}/{model_id}/{original|onnx|converted|benchmarks|logs}/...
resource "aws_s3_bucket" "models" {
  bucket = "${local.name}-models"
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket                  = aws_s3_bucket.models.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── EventBridge: routes new ONNX uploads to format-specific queues ─
resource "aws_cloudwatch_event_rule" "model_uploaded" {
  name = "${local.name}-model-uploaded"
  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [aws_s3_bucket.models.bucket] }
      object = { key = [{ prefix = "models/" }, { suffix = "/onnx/model.onnx" }] }
    }
  })
}

resource "aws_s3_bucket_notification" "models_eventbridge" {
  bucket      = aws_s3_bucket.models.id
  eventbridge = true
}

# ── SQS: one isolated queue per conversion format, each with a DLQ ─
module "tflite_queue" {
  source     = "./modules/queue_with_dlq"
  queue_name = "${local.name}-tflite"
}

module "tensorrt_queue" {
  source     = "./modules/queue_with_dlq"
  queue_name = "${local.name}-tensorrt"
}

module "coreml_queue" {
  source     = "./modules/queue_with_dlq"
  queue_name = "${local.name}-coreml"
}

resource "aws_cloudwatch_event_target" "to_tflite" {
  rule      = aws_cloudwatch_event_rule.model_uploaded.name
  target_id = "tflite-queue"
  arn       = module.tflite_queue.queue_arn
}

resource "aws_cloudwatch_event_target" "to_tensorrt" {
  rule      = aws_cloudwatch_event_rule.model_uploaded.name
  target_id = "tensorrt-queue"
  arn       = module.tensorrt_queue.queue_arn
}

resource "aws_cloudwatch_event_target" "to_coreml" {
  rule      = aws_cloudwatch_event_rule.model_uploaded.name
  target_id = "coreml-queue"
  arn       = module.coreml_queue.queue_arn
}

# ── ECR: one repository per container image ────────────────────
resource "aws_ecr_repository" "backend" {
  name = "${local.name}-backend"
}

resource "aws_ecr_repository" "frontend" {
  name = "${local.name}-frontend"
}

resource "aws_ecr_repository" "tflite_worker" {
  name = "${local.name}-tflite-worker"
}

resource "aws_ecr_repository" "tensorrt_worker" {
  name = "${local.name}-tensorrt-worker"
}

resource "aws_ecr_repository" "coreml_worker" {
  name = "${local.name}-coreml-worker"
}

# ── RDS PostgreSQL ───────────────────────────────────────────────
resource "aws_db_subnet_group" "this" {
  name       = "${local.name}-db-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_security_group" "rds" {
  name   = "${local.name}-rds"
  vpc_id = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres" {
  identifier             = "${local.name}-db"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  db_name                = "modelforge"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true
  storage_encrypted      = true
}

# ── ECS cluster + shared networking ─────────────────────────────
resource "aws_ecs_cluster" "this" {
  name = local.name
}

resource "aws_security_group" "ecs_tasks" {
  name   = "${local.name}-ecs-tasks"
  vpc_id = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# GPU-enabled capacity provider for the TensorRT worker only.
resource "aws_ecs_capacity_provider" "gpu" {
  name = "${local.name}-gpu"
  auto_scaling_group_provider {
    auto_scaling_group_arn = aws_autoscaling_group.gpu.arn
    managed_scaling {
      status          = "ENABLED"
      target_capacity = 100
    }
  }
}

resource "aws_launch_template" "gpu" {
  name_prefix   = "${local.name}-gpu-"
  image_id      = "ami-0000000000000000" # replace with the current ECS GPU-optimized AMI
  instance_type = "g4dn.xlarge"
}

resource "aws_autoscaling_group" "gpu" {
  name                = "${local.name}-gpu-asg"
  vpc_zone_identifier = var.private_subnet_ids
  min_size            = 0
  max_size            = 2
  desired_capacity    = 0
  launch_template {
    id      = aws_launch_template.gpu.id
    version = "$Latest"
  }
}

# ── CloudWatch log groups ────────────────────────────────────────
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name}/backend"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "tflite_worker" {
  name              = "/ecs/${local.name}/tflite-worker"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "tensorrt_worker" {
  name              = "/ecs/${local.name}/tensorrt-worker"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "coreml_worker" {
  name              = "/ecs/${local.name}/coreml-worker"
  retention_in_days = 30
}
