aws_region = "ap-south-1"
name_prefix = "myapp-prod"
vpc_cidr = "10.2.0.0/16"
az_count = 2
single_nat_gateway = false  # PROD: NAT per AZ for HA
app_port = 5000
#acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
