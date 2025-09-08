aws_region = "ap-south-1"
name_prefix = "myapp-dev"
vpc_cidr = "10.1.0.0/16"
az_count = 2
single_nat_gateway = true   # DEV: single NAT to reduce cost
app_port = 5000
acm_certificate_arn = ""
