# outputs.tf
output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnets" {
  value = module.network.public_subnet_ids
}

output "private_subnets" {
  value = module.network.private_subnet_ids
}

output "alb_dns" {
  value = module.alb.alb_dns_name
}

output "alb_arn" {
  value = module.alb.alb_arn
}

output "ecs_service_sg" {
  value = module.security.ecs_service_sg_id
}

output "rds_sg" {
  value = module.security.rds_sg_id
}
