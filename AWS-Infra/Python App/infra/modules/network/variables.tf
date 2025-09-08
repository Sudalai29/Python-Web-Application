# modules/network/variables.tf
variable "name_prefix" {
  description = "Prefix for resource names (e.g., project env)"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "How many AZs to create subnets in"
  type        = number
  default     = 2
}

variable "single_nat_gateway" {
  description = "If true create single NAT gateway (dev-mode). If false create NAT per AZ (prod-mode)"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags map to apply to resources"
  type        = map(string)
  default     = {}
}
