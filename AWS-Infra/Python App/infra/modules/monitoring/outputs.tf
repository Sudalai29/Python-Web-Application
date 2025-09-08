output "ecs_log_group_name" { value = aws_cloudwatch_log_group.ecs.name }
output "alb_log_group_name" { value = aws_cloudwatch_log_group.alb.name }
output "rds_log_group_name" { value = aws_cloudwatch_log_group.rds.name }

