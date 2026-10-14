# CPU conversion worker: one Fargate task polling the cpu queue.

resource "aws_ecr_repository" "cpu_worker" {
  name         = "${local.name}-cpu-worker"
  force_delete = true # lets `terraform destroy` remove it with images inside
}

resource "aws_ecr_lifecycle_policy" "cpu_worker" {
  repository = aws_ecr_repository.cpu_worker.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the 3 newest images (ECR storage is billed)"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 3 }
      action       = { type = "expire" }
    }]
  })
}

resource "aws_cloudwatch_log_group" "cpu_worker" {
  name              = "/ecs/${local.name}/cpu-worker"
  retention_in_days = 7
}

resource "aws_ecs_cluster" "this" {
  name = local.name
}

resource "aws_security_group" "workers" {
  name        = "${local.name}-workers"
  description = "ECS workers: no inbound, outbound to ECR/S3/SQS/RDS"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_task_definition" "cpu_worker" {
  family                   = "${local.name}-cpu-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024 # 1 vCPU
  memory                   = 4096 # onnx2tf + TensorFlow need ~3 GB for ResNet-sized models
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.cpu_worker.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([{
    name      = "cpu-worker"
    image     = "${aws_ecr_repository.cpu_worker.repository_url}:${var.worker_image_tag}"
    essential = true
    environment = [
      { name = "AWS_MODE", value = "aws" },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "S3_BUCKET", value = aws_s3_bucket.models.bucket },
      { name = "SQS_CPU_QUEUE", value = module.cpu_queue.queue_name },
      { name = "SQS_TENSORRT_QUEUE", value = module.tensorrt_queue.queue_name },
      # ponytail: password passed as a plain env var (visible in the task definition); move to Secrets Manager (~$0.40/month) for real production.
      { name = "DATABASE_URL", value = "postgresql+psycopg://modelforge:${var.db_password}@${aws_db_instance.postgres.endpoint}/modelforge" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.cpu_worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "cpu-worker"
      }
    }
  }])
}

resource "aws_ecs_service" "cpu_worker" {
  name            = "${local.name}-cpu-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.cpu_worker.arn
  desired_count   = var.cpu_worker_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.workers.id]
    assign_public_ip = true # reach ECR/S3/SQS without a NAT gateway
  }
}
