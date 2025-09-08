variable "name_prefix" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "rds_sg_id" { type = string }
variable "db_name" {
  type    = string
  default = "myapp"
}
variable "db_username" {
  type    = string
  default = "appuser"
}
variable "engine" {
  type    = string
  default = "postgres"
}
variable "engine_version" {
  type    = string
  default = "11"
}
variable "allocated_storage" {
  type    = number
  default = 20
}
variable "instance_class" { 
 type = string 
 default = "db.t3.micro" 
}
variable "multi_az" { 
 type = bool
 default = false 
}
variable "db_port" { 
 type = number
 default = 5432 
}

variable "tags" {
  type    = map(string)
  default = {}
}

