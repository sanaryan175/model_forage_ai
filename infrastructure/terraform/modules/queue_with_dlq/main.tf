variable "queue_name" {
  type = string
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.queue_name}-dlq"
  message_retention_seconds = 1209600 # 14 days, to inspect jobs that failed 3 times
}

resource "aws_sqs_queue" "this" {
  name                       = var.queue_name
  visibility_timeout_seconds = 900 # >= worst-case conversion time, so a running job isn't handed out twice
  receive_wait_time_seconds  = 10  # long polling: fewer empty (billed) receives
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

output "queue_arn" {
  value = aws_sqs_queue.this.arn
}

output "queue_name" {
  value = aws_sqs_queue.this.name
}
