# modules/security/variables.tf
variable "vpc_id" {
  type        = string
  description = "VPC id"
}

variable "name_prefix" {
  type        = string
  description = "Resource name prefix"
}

variable "app_port" {
  type        = number
  description = "Port the app listens on (ECS task port)"
  default     = 5000
}

variable "db_port" {
  type        = number
  description = "Database port (Postgres default)"
  default     = 5432
}

variable "tags" {
  type        = map(string)
  default     = {}
}
