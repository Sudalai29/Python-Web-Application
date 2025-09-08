locals {
  secrets_arns = var.env == "prod" ? var.secrets_arns_prod : var.secrets_arns_dev
}

resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"
  tags = merge(var.tags, { Name = "${var.name_prefix}-cluster" })
}

resource "aws_ecs_task_definition" "this" {
  family                   = "${var.name_prefix}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([{
    name      = var.container_name
    #image     = var.image
    image     = "${var.ecr_repo_url}:latest"
    essential = true
    portMappings = [{
      containerPort = var.container_port
      protocol      = "tcp"
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = var.log_group_name   # <-- pass from monitoring module
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = var.container_name
      }
    }
    secrets = [
      for key, arn in var.secrets_arns : {
        name      = key
        valueFrom = arn
      }
    ] 
  }])
   lifecycle {
    ignore_changes = [container_definitions] 
  }
}

resource "aws_ecs_service" "this" {
  name            = "${var.name_prefix}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [var.ecs_sg_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.alb_target_group_arn
    container_name   = var.container_name
    container_port   = var.container_port
  }
}

