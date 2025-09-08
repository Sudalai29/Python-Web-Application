output "rds_endpoint" { value = aws_db_instance.this.endpoint }
output "rds_secret_arn" { value = aws_secretsmanager_secret.rds.arn }
output "rds_secret_name" {
  value = aws_secretsmanager_secret.rds.name
}