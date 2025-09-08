resource "random_password" "rds_password" {
  length  = 16
  special = true
}

# Secret definition
resource "aws_secretsmanager_secret" "rds" {
  name        = "${var.name_prefix}-db-secret"
  description = "RDS DB credentials for ${var.name_prefix}"
  tags        = merge(var.tags, { Name = "${var.name_prefix}-db-secret" })
}

# Initial secret value
resource "aws_secretsmanager_secret_version" "rds" {
  secret_id     = aws_secretsmanager_secret.rds.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.rds_password.result
    host     = aws_db_instance.this.address
    port     = var.db_port
    dbname   = var.db_name
  })

  depends_on = [aws_db_instance.this]
}
    

# RDS Subnet Group
resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags       = merge(var.tags, { Name = "${var.name_prefix}-db-subnet-group" })
}

# RDS Instance
resource "aws_db_instance" "this" {
  identifier             = "${var.name_prefix}-db"
  allocated_storage      = var.allocated_storage
  engine                 = var.engine
  engine_version         = var.engine_version
  instance_class         = var.instance_class
  username               = var.db_username
  password               = random_password.rds_password.result
  port                   = var.db_port
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [var.rds_sg_id]
  multi_az               = var.multi_az
  publicly_accessible    = false
  skip_final_snapshot    = true
  tags                   = merge(var.tags, { Name = "${var.name_prefix}-db" })
  enabled_cloudwatch_logs_exports = [
    "postgresql",  
  ]
}
