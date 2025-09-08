# Python Application Infrastructure on AWS

A complete containerized Python application deployed on AWS using Terraform, featuring automated CI/CD, high availability, and production-ready monitoring.

## 🚀 Features

### Infrastructure
- **High Availability**: Multi-AZ deployment across 2 availability zones
- **Auto Scaling**: ECS Fargate with configurable scaling policies
- **Security**: Network isolation with security groups and private subnets
- **Monitoring**: Complete CloudWatch integration with logs and metrics
- **SSL/TLS**: HTTPS support with ACM certificate integration
- **Database**: Managed PostgreSQL RDS with automated backups
- **Secrets Management**: AWS Secrets Manager for secure credential storage

### CI/CD Pipeline
- **Automated Builds**: GitHub Actions workflow for containerization
- **Container Registry**: Amazon ECR for Docker image storage
- **Zero-Downtime Deployments**: Rolling updates with health checks
- **Environment Separation**: Support for dev/staging/prod environments

## 📁 Repository Structure

```
.
├── main.tf                     # Root Terraform configuration
├── variables.tf                # Root variables
├── modules/
│   ├── network/               # VPC, subnets, routing
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── security/              # Security groups
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── alb/                   # Application Load Balancer
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── ecr/                   # Container registry
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── ecs/                   # Container orchestration
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── rds/                   # PostgreSQL database
│   │   ├── main.tf
│   │   └── variables.tf
│   └── monitoring/            # CloudWatch setup
│       ├── main.tf
│       └── variables.tf
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI/CD pipeline
├── app/                       # Python application code
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── README.md
```

## 🛠️ Technology Stack

### Infrastructure
- **IaC**: Terraform with modular architecture
- **Cloud Provider**: AWS
- **Networking**: VPC, Application Load Balancer, NAT Gateway
- **Compute**: ECS Fargate (serverless containers)
- **Database**: Amazon RDS PostgreSQL
- **Storage**: Amazon ECR for container images
- **Security**: AWS Secrets Manager, Security Groups
- **Monitoring**: CloudWatch Logs & Metrics

### Application
- **Runtime**: Python 3.x
- **Framework**: Flask/FastAPI
- **Database**: PostgreSQL
- **Containerization**: Docker
- **Port**: 5000 (configurable)

### DevOps
- **CI/CD**: GitHub Actions
- **State Management**: S3 backend with DynamoDB locking
- **Environment Management**: Terraform workspaces

## ⚙️ Configuration
### Security Configuration

#### Network Security
- **ALB Security Group**: Allows HTTP (80) and HTTPS (443) from internet
- **ECS Security Group**: Allows traffic only from ALB on port 5000
- **RDS Security Group**: Allows PostgreSQL (5432) only from ECS tasks

#### IAM Roles
- **ECS Execution Role**: ECR image pulling, CloudWatch logging
- **ECS Task Role**: Secrets Manager access for database credentials

## 🚦 Deployment

### Prerequisites
1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.0
3. **AWS CLI** configured
4. **Docker** for local testing
5. **GitHub repository** with Actions enabled

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Configure Terraform backend**
   ```bash
   # Create S3 bucket and DynamoDB table for state management
   aws s3 mb s3://my-terraform-state-smd29-py
   aws dynamodb create-table \
     --table-name terraform-lock-table \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
   ```

3. **Initialize Terraform**
   ```bash
   terraform init
   ```

4. **Create workspace (optional)**
   ```bash
   terraform workspace new dev
   terraform workspace new prod
   ```

### Deployment Commands

```bash
# Plan deployment
terraform plan

# Apply infrastructure
terraform apply

# Get outputs
terraform output

# Destroy infrastructure
terraform destroy
```

### CI/CD Pipeline

The GitHub Actions workflow automatically:
1. **Builds** Docker image from your Python application
2. **Pushes** to ECR repository
3. **Updates** ECS service with new image
4. **Performs** health checks and rollback if needed

Set up these GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## 📊 Monitoring & Logging

### CloudWatch Integration
- **Application Logs**: Centralized container logging
- **Infrastructure Metrics**: ECS, ALB, RDS performance metrics
- **Custom Alarms**: CPU, memory, database connection monitoring
- **Log Retention**: Configurable retention periods

### Health Checks
- **ALB Health Check**: `/health` endpoint monitoring
- **ECS Service Health**: Container health and restart policies
- **RDS Monitoring**: Database performance and connectivity

```

## 🐛 Troubleshooting

### Common Issues

**ECS Tasks Not Starting**
- Check CloudWatch logs: `/aws/ecs/<cluster-name>`
- Verify ECR image exists and is accessible
- Check IAM permissions for task roles

**ALB Health Check Failures**
- Ensure `/health` endpoint returns 200 status
- Verify security group allows traffic on port 5000
- Check ECS task health and logs

**Database Connection Issues**
- Verify RDS security group allows ECS access
- Check Secrets Manager permissions
- Validate database credentials in secrets

**Terraform State Issues**
- Ensure S3 bucket and DynamoDB table exist
- Check AWS credentials and permissions
- Verify backend configuration in `main.tf`

### Useful Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster <cluster-name> --services <service-name>

# View ECS task logs
aws logs get-log-events --log-group-name <log-group> --log-stream-name <stream>

# Test ALB endpoint
curl -I http://<alb-dns-name>/health

# Check RDS connectivity
psql -h <rds-endpoint> -U <username> -d <database>
```

<img width="3109" height="832" alt="AWS_Infra" src="https://github.com/user-attachments/assets/ab8605e6-192e-4fe8-81d1-310bf210eae5" />
