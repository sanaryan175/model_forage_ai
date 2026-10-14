variable "project" {
  description = "Prefix for every resource name"
  type        = string
  default     = "modelforge"
}

variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "aws_profile" {
  description = "AWS CLI profile Terraform uses (aws configure --profile ...)"
  type        = string
  default     = "modelforge"
}

variable "db_password" {
  description = "RDS master password. Put it in terraform.tfvars (git-ignored), never in code."
  type        = string
  sensitive   = true
}

variable "my_ip_cidr" {
  description = "Your laptop's public IP as x.x.x.x/32, the only outside address allowed to reach the database"
  type        = string
}

variable "cpu_worker_count" {
  description = "Running CPU workers. Each costs ~$0.06/hour; set to 0 when not using the cloud pipeline."
  type        = number
  default     = 1
}

variable "worker_image_tag" {
  type    = string
  default = "latest"
}
