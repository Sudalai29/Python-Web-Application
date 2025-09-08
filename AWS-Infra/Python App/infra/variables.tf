# variables.tf
variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "name_prefix" {
  description = "Prefix for resources (e.g., project-env like myapp-dev)"
  type        = string
  default     = "myapp"
}

variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of AZs (subnet groups) to create"
  type        = number
  default     = 2
}

variable "single_nat_gateway" {
  description = "Create single NAT gateway (dev) or NAT per AZ (prod)"
  type        = bool
  default     = true
}

variable "app_port" {
  type    = number
  default = 5000
}

variable "db_port" {
  type    = number
  default = 5432
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "acm_certificate_arn" {
  type    = string
  default = ""
}

variable "instance_class" { 
 type = string 
 default = "db.t3.micro" 
}

variable "tags" {
  type        = map(string)
  description = "Base tags applied to all resources"
  default     = {
    ManagedBy = "terraform"
  }
}

variable "desired_count" {
  type    = number
  default = 1
}
variable "cpu" {
  type    = string
  default = "256"
}
variable "memory" {
  type    = string
  default = "512"
}

locals {
  tags = merge(
    var.tags,
    {
      Environment = terraform.workspace
    }
  )
}

