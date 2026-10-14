# Values to copy into backend/.env (AWS mode) after `terraform apply`.

output "s3_bucket" {
  value = aws_s3_bucket.models.bucket
}

output "sqs_cpu_queue" {
  value = module.cpu_queue.queue_name
}

output "sqs_tensorrt_queue" {
  value = module.tensorrt_queue.queue_name
}

output "ecr_cpu_worker_url" {
  value = aws_ecr_repository.cpu_worker.repository_url
}

output "ecs_cluster" {
  value = aws_ecs_cluster.this.name
}

output "database_url" {
  value     = "postgresql+psycopg://modelforge:${var.db_password}@${aws_db_instance.postgres.endpoint}/modelforge"
  sensitive = true # show with: terraform output -raw database_url
}
