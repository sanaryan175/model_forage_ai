locals {
  region_env = { name = "AWS_REGION", value = var.aws_region }
  aws_mode_env = { name = "AWS_MODE", value = "aws" }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.backend_task.arn

  container_definitions = jsonencode([{
    name  = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:${var.container_image_tag}"
    portMappings = [{ containerPort = 8000 }]
    environment = [
      local.aws_mode_env,
      local.region_env,
      { name = "S3_BUCKET", value = aws_s3_bucket.models.bucket },
      { name = "SQS_TFLITE_QUEUE", value = module.tflite_queue.queue_url },
      { name = "SQS_TENSORRT_QUEUE", value = module.tensorrt_queue.queue_url },
      { name = "SQS_COREML_QUEUE", value = module.coreml_queue.queue_url },
      { name = "DATABASE_URL", value = "postgresql+psycopg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/modelforge" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name            = "${local.name}-backend"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.ecs_tasks.id]
  }
}

resource "aws_ecs_task_definition" "tflite_worker" {
  family                   = "${local.name}-tflite-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.worker_task["tflite"].arn

  container_definitions = jsonencode([{
    name  = "tflite-worker"
    image = "${aws_ecr_repository.tflite_worker.repository_url}:${var.container_image_tag}"
    environment = [
      local.aws_mode_env,
      local.region_env,
      { name = "S3_BUCKET", value = aws_s3_bucket.models.bucket },
      { name = "SQS_TFLITE_QUEUE", value = module.tflite_queue.queue_url },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.tflite_worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "tflite-worker"
      }
    }
  }])
}

resource "aws_ecs_service" "tflite_worker" {
  name            = "${local.name}-tflite-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.tflite_worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.ecs_tasks.id]
  }
}

resource "aws_ecs_task_definition" "coreml_worker" {
  family                   = "${local.name}-coreml-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.worker_task["coreml"].arn

  container_definitions = jsonencode([{
    name  = "coreml-worker"
    image = "${aws_ecr_repository.coreml_worker.repository_url}:${var.container_image_tag}"
    environment = [
      local.aws_mode_env,
      local.region_env,
      { name = "S3_BUCKET", value = aws_s3_bucket.models.bucket },
      { name = "SQS_COREML_QUEUE", value = module.coreml_queue.queue_url },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.coreml_worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "coreml-worker"
      }
    }
  }])
}

resource "aws_ecs_service" "coreml_worker" {
  name            = "${local.name}-coreml-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.coreml_worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.ecs_tasks.id]
  }
}

# TensorRT requires a GPU, so it runs on the EC2+GPU capacity provider instead of Fargate.
resource "aws_ecs_task_definition" "tensorrt_worker" {
  family                   = "${local.name}-tensorrt-worker"
  requires_compatibilities = ["EC2"]
  network_mode             = "bridge"
  cpu                      = 2048
  memory                   = 4096
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.worker_task["tensorrt"].arn

  container_definitions = jsonencode([{
    name  = "tensorrt-worker"
    image = "${aws_ecr_repository.tensorrt_worker.repository_url}:${var.container_image_tag}"
    resourceRequirements = [{ type = "GPU", value = "1" }]
    environment = [
      local.aws_mode_env,
      local.region_env,
      { name = "S3_BUCKET", value = aws_s3_bucket.models.bucket },
      { name = "SQS_TENSORRT_QUEUE", value = module.tensorrt_queue.queue_url },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.tensorrt_worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "tensorrt-worker"
      }
    }
  }])
}

resource "aws_ecs_service" "tensorrt_worker" {
  name                = "${local.name}-tensorrt-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.tensorrt_worker.arn
  desired_count   = 0 # scaled up on demand; see capacity provider managed scaling

  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.gpu.name
    weight            = 1
  }
}
