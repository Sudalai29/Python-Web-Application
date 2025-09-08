# CloudWatch Log Groups

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.name_prefix}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "alb" {
  name              = "/alb/${var.name_prefix}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "rds" {
  name              = "/rds/${var.name_prefix}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}
