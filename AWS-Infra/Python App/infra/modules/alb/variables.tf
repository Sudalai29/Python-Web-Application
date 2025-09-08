# modules/alb/variables.tf
variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "alb_sg_id" {
  type = string
}

variable "target_group_port" {
  type    = number
  default = 5000
}

variable "target_type" {
  type    = string
  default = "ip" # for Fargate tasks
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "health_check_interval" {
  type    = number
  default = 30
}

variable "health_check_timeout" {
  type    = number
  default = 5
}

variable "health_check_healthy_threshold" {
  type    = number
  default = 3
}

variable "health_check_unhealthy_threshold" {
  type    = number
  default = 2
}

variable "health_check_matcher" {
  type    = string
  default = "200-399"
}

variable "acm_certificate_arn" {
  type    = string
  default = ""
}

variable "idle_timeout" {
  type    = number
  default = 60
}

variable "tags" {
  type    = map(string)
  default = {}
}
