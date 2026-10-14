# Least privilege: the worker can only touch the model bucket and its own queue.

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Used by ECS itself to pull the image from ECR and write CloudWatch logs.
resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Used by the worker code (boto3) at runtime.
data "aws_iam_policy_document" "cpu_worker" {
  statement {
    sid       = "ModelBucket"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.models.arn}/*"]
  }
  statement {
    sid       = "ModelBucketHeadObject" # exists() calls HeadObject, which needs ListBucket to report 404 instead of 403
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.models.arn]
  }
  statement {
    sid       = "ConsumeOwnQueue"
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueUrl", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]
    resources = [module.cpu_queue.queue_arn]
  }
}

resource "aws_iam_role" "cpu_worker" {
  name               = "${local.name}-cpu-worker"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy" "cpu_worker" {
  role   = aws_iam_role.cpu_worker.id
  policy = data.aws_iam_policy_document.cpu_worker.json
}
