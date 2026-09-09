# Least-privilege IAM: each ECS task gets only the permissions its job actually needs.

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Backend API task role: read/write its own S3 prefix, publish to SQS, full RDS access
# via network security group (not IAM).
data "aws_iam_policy_document" "backend_task" {
  statement {
    sid       = "ModelBucketReadWrite"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.models.arn, "${aws_s3_bucket.models.arn}/*"]
  }
  statement {
    sid = "PublishConversionJobs"
    actions = ["sqs:SendMessage"]
    resources = [
      module.tflite_queue.queue_arn,
      module.tensorrt_queue.queue_arn,
      module.coreml_queue.queue_arn,
    ]
  }
}

resource "aws_iam_role" "backend_task" {
  name               = "${local.name}-backend-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy" "backend_task" {
  role   = aws_iam_role.backend_task.id
  policy = data.aws_iam_policy_document.backend_task.json
}

# Worker task role factory: each format worker can only read the bucket and consume
# from + delete messages on its own queue — never another format's queue.
data "aws_iam_policy_document" "worker_task" {
  for_each = {
    tflite   = module.tflite_queue.queue_arn
    tensorrt = module.tensorrt_queue.queue_arn
    coreml   = module.coreml_queue.queue_arn
  }

  statement {
    sid       = "ReadWriteModelBucket"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.models.arn}/*"]
  }
  statement {
    sid       = "ConsumeOwnQueue"
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [each.value]
  }
}

resource "aws_iam_role" "worker_task" {
  for_each           = data.aws_iam_policy_document.worker_task
  name               = "${local.name}-${each.key}-worker-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy" "worker_task" {
  for_each = data.aws_iam_policy_document.worker_task
  role     = aws_iam_role.worker_task[each.key].id
  policy   = each.value.json
}
