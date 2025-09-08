variable "name_prefix" { type = string }
variable "aws_region" { type = string }
variable "ecs_cluster_name" { type = string }
variable "alb_name" { type = string }
variable "rds_identifier" { type = string }
variable "log_retention_days" {
  type    = number
  default = 14
}

variable "tags" {
  type    = map(string)
  default = {}
}
