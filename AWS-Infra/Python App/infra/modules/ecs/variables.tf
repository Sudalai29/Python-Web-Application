variable "name_prefix" { type = string }
variable "ecs_sg_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "alb_target_group_arn" { type = string }
variable "container_name" {
  type    = string
  default = "app"
}
variable "container_port" {
  type    = number
  default = 5000
}
variable "image" {
  type = string
}
variable "cpu" {
  type    = string
  default = "256"
}
variable "memory" {
  type    = string
  default = "512"
}
variable "desired_count" {
  type    = number
  default = 1
}
variable "execution_role_arn" {
  type = string
}
variable "task_role_arn" {
  type = string
}
variable "secrets_arns" {
  type    = map(string)
  default = {}
}
variable "tags" {
  type    = map(string)
  default = {}
}
variable "log_group_name" {
  description = "CloudWatch Log Group name for ECS container logs"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "ecr_repo_url" {
  type        = string
  description = "ECR repository URL for Docker image"
}

variable "env" {
  description = "Environment: dev or prod"
  type        = string
}

variable "secrets_arns_dev" {
  type        = map(string)
  description = "Map of dev secrets"
}

variable "secrets_arns_prod" {
  type        = map(string)
  description = "Map of prod secrets"
}
