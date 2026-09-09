output "s3_bucket_name" {
  value = aws_s3_bucket.models.bucket
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "rds_endpoint" {
  value     = aws_db_instance.postgres.endpoint
  sensitive = true
}

output "ecr_repository_urls" {
  value = {
    backend         = aws_ecr_repository.backend.repository_url
    frontend        = aws_ecr_repository.frontend.repository_url
    tflite_worker   = aws_ecr_repository.tflite_worker.repository_url
    tensorrt_worker = aws_ecr_repository.tensorrt_worker.repository_url
    coreml_worker   = aws_ecr_repository.coreml_worker.repository_url
  }
}

output "sqs_queue_urls" {
  value = {
    tflite   = module.tflite_queue.queue_url
    tensorrt = module.tensorrt_queue.queue_url
    coreml   = module.coreml_queue.queue_url
  }
}
