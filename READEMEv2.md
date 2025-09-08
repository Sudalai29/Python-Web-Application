# Flask Application Documentation

A production-ready Flask web application for collecting and managing user quotes and advice, integrated with AWS services and PostgreSQL database.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [AWS Integration](#aws-integration)
- [Security](#security)
- [Error Handling](#error-handling)
- [Deployment](#deployment)
- [Monitoring](#monitoring)

## 🎯 Overview

This Flask application provides a web interface for users to:
- Submit personal quotes and advice
- Search and view submitted entries
- Delete existing entries
- All data is stored in a PostgreSQL database with AWS Secrets Manager integration

**Application Type**: Web Application (CRUD Operations)  
**Framework**: Flask with WTForms  
**Database**: PostgreSQL with connection pooling  
**Cloud Integration**: AWS Secrets Manager  
**Port**: 5000 (configurable)

## ✨ Features

### Core Functionality
- **User Data Collection**: Forms to capture name, quote, and advice
- **Data Persistence**: PostgreSQL database with upsert operations
- **Search Capability**: Name-based search with partial matching
- **Data Management**: Delete functionality for existing entries
- **Responsive Design**: HTML templates with form validation

### Production Features
- **Connection Pooling**: Efficient database connection management
- **Environment-Aware**: Dev/Prod configuration support
- **Health Checks**: Built-in health endpoint for load balancer monitoring
- **CSRF Protection**: Security against cross-site request forgery
- **Logging**: Structured logging for debugging and monitoring
- **Error Handling**: Graceful error handling with user feedback

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Flask App      │    │   PostgreSQL    │
│   (Health Check)│───▶│   (Port 5000)    │───▶│   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  AWS Secrets     │
                       │  Manager         │
                       └──────────────────┘
```

### Component Flow
1. **Load Balancer** → Health check endpoint (`/health`)
2. **User Request** → Flask routes → Form validation
3. **Database Operation** → Connection pool → PostgreSQL
4. **Secrets** → AWS Secrets Manager → Database credentials

## 📦 Dependencies

### Python Packages
```python
Flask==2.x              # Web framework
Flask-WTF==1.x          # Form handling and CSRF protection
WTForms==3.x            # Form validation
psycopg2-binary==2.x    # PostgreSQL adapter
boto3==1.x              # AWS SDK
```

### System Requirements
- Python 3.8+
- PostgreSQL 11+
- AWS credentials (IAM role or access keys)
- 512MB+ RAM recommended

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Deployment environment (dev/prod) | `dev` | No |
| `REGION_NAME` | AWS region for Secrets Manager | `ap-south-1` | No |
| `FLASK_SECRET_KEY` | Flask session encryption key | `supersecretkey` | Yes (Prod) |

### Secret Management
```python
SECRET_MAP = {
    "dev": "myapp-dev-db-secret",
    "prod": "myapp-prod-db-secret"
}
```

### Connection Pool Settings
- **Minimum Connections**: 1
- **Maximum Connections**: 5
- **Automatic reconnection**: Yes

## 🗄️ Database Schema

### Table: `user_details`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `name` | `VARCHAR(255)` | PRIMARY KEY | User's name (unique) |
| `quote` | `TEXT` | NOT NULL | User's favorite quote |
| `advice` | `TEXT` | NOT NULL | User's advice |
| `created_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Entry creation time |

### Database Operations
- **UPSERT**: Insert new records or update existing ones based on name
- **SEARCH**: Case-insensitive partial name matching with ILIKE
- **DELETE**: Remove records by name
- **PAGINATION**: Limit results to 50 entries

### SQL Examples
```sql
-- Insert or Update
INSERT INTO user_details (name, quote, advice)
VALUES (%s, %s, %s)
ON CONFLICT (name)
DO UPDATE SET quote = EXCLUDED.quote, advice = EXCLUDED.advice, created_at = CURRENT_TIMESTAMP

-- Search
SELECT name, quote, advice, created_at
FROM user_details
WHERE name ILIKE %search_term%
ORDER BY created_at DESC
LIMIT 50

-- Delete
DELETE FROM user_details WHERE name = %s
```

## 🛠️ API Endpoints

### `GET /` - Home Page
**Purpose**: Display form for new submissions  
**Template**: `index.html`  
**Form**: UserForm with CSRF protection

**Response**:
```html
<!-- Renders form with fields: username, quote, advice, submit -->
```

### `POST /` - Submit Data
**Purpose**: Process form submission and save to database  
**Validation**: WTForms validators (DataRequired, Length)  
**Redirect**: `/output` on success

**Form Data**:
```json
{
  "username": "string (max 255 chars)",
  "quote": "string (max 500 chars)", 
  "advice": "string (max 500 chars)"
}
```

### `GET /output` - View Data
**Purpose**: Display all entries with search functionality  
**Template**: `response.html`  
**Query Parameters**:
- `search`: Optional name filter

**Response Data**:
```python
{
  "users": [
    {
      "name": "John Doe",
      "quote": "Be yourself",
      "advice": "Always stay positive", 
      "created_at": "01 Sep 2025 10:30:45"
    }
  ],
  "search": "search_term"
}
```

### `POST /delete/<name>` - Delete Entry
**Purpose**: Remove user entry by name  
**Method**: POST (CSRF protected)  
**Redirect**: `/output` with flash message

### `GET /health` - Health Check
**Purpose**: Load balancer health monitoring  
**Response**: `"OK"` with HTTP 200  
**Used by**: ALB target group health checks

## ☁️ AWS Integration

### Secrets Manager Integration
```python
def get_db_secret():
    """Retrieve database credentials from AWS Secrets Manager"""
    client = boto3.client("secretsmanager", region_name=REGION_NAME)
    response = client.get_secret_value(SecretId=SECRET_NAME)
    return json.loads(response['SecretString'])
```

### Expected Secret Format
```json
{
  "dbname": "myapp_db",
  "username": "appuser", 
  "password": "generated_password",
  "host": "myapp-db.region.rds.amazonaws.com",
  "port": 5432
}
```

### IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:region:account:secret:myapp-*-db-secret-*"
    }
  ]
}
```

## 🔒 Security

### CSRF Protection
```python
from flask_wtf import CSRFProtect
csrf = CSRFProtect(app)
```
- All forms include CSRF tokens
- POST requests validated automatically
- Prevents cross-site request forgery attacks

### Input Validation
```python
class UserForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired(), Length(max=255)])
    quote = TextAreaField("Quote", validators=[DataRequired(), Length(max=500)])
    advice = TextAreaField("Advice", validators=[DataRequired(), Length(max=500)])
```

### SQL Injection Prevention
- **Parameterized Queries**: All database operations use parameter binding
- **Input Sanitization**: Form validation prevents malicious input
- **Connection Pooling**: Secure connection management

### Security Headers
Recommended additions for production:
```python
from flask_talisman import Talisman
Talisman(app)  # Adds security headers
```

## 🚨 Error Handling

### Database Errors
```python
try:
    # Database operation
    conn.commit()
    flash("✅ Data saved successfully!", "success")
except Exception as e:
    logging.error(f"Error saving user: {e}")
    flash("⚠️ Failed to save data. Try again.", "danger")
```

### Common Error Scenarios
- **Connection Pool Exhaustion**: Automatic retry with exponential backoff
- **Database Unavailable**: Graceful degradation with user notification
- **Invalid Input**: Form validation with field-specific error messages
- **AWS Secrets Access**: Startup failure with detailed logging

### Logging Strategy
```python
logging.basicConfig(level=logging.INFO)
logging.info("DB connection pool initialized")
logging.error(f"Failed to retrieve secret: {e}")
```

## 🚀 Deployment

### Container Configuration
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

### Environment Setup
```bash
# Development
export ENVIRONMENT=dev
export REGION_NAME=ap-south-1
export FLASK_SECRET_KEY=your-secret-key

# Production (set via ECS task definition)
{
  "environment": [
    {"name": "ENVIRONMENT", "value": "prod"},
    {"name": "REGION_NAME", "value": "ap-south-1"}
  ],
  "secrets": [
    {"name": "FLASK_SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
  ]
}
```

### Health Check Configuration
```yaml
# ECS Task Definition Health Check
healthCheck:
  command: ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"]
  interval: 30
  timeout: 5
  retries: 3
```

## 📊 Monitoring

### Application Metrics
- **Response Time**: Track endpoint performance
- **Error Rate**: Monitor failed requests
- **Database Connections**: Pool utilization
- **Memory Usage**: Container resource consumption

### CloudWatch Integration
```python
# Structured logging for CloudWatch
import json
logging.info(json.dumps({
    "event": "user_created", 
    "user": name,
    "timestamp": datetime.now().isoformat()
}))
```

### Key Performance Indicators
- **Uptime**: Health check success rate
- **Throughput**: Requests per minute
- **Database Performance**: Query execution time
- **User Activity**: Form submissions per day

## 🛠️ Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up local PostgreSQL
createdb myapp_local

# Set environment variables
export ENVIRONMENT=dev
export DATABASE_URL=postgresql://user:pass@localhost/myapp_local

# Run application
python app.py
```

### Testing Endpoints
```bash
# Health check
curl http://localhost:5000/health

# Form submission (requires CSRF token)
curl -X POST http://localhost:5000/ \
  -d "username=test&quote=hello&advice=world&csrf_token=..."

# View data
curl http://localhost:5000/output?search=test
```

### Database Migrations
```python
# Add new columns
ALTER TABLE user_details ADD COLUMN email VARCHAR(255);

# Update application code to handle new field
# Deploy with backward compatibility
```

## 🔧 Troubleshooting

### Common Issues

**Connection Pool Errors**
```python
# Check pool status
print(f"Pool stats: {_db_pool.closed}")
```

**Secret Manager Access Denied**
- Verify IAM role permissions
- Check secret name matches environment
- Confirm AWS region settings

**Database Connection Timeout**
- Verify RDS security group allows ECS access
- Check database endpoint and port
- Test connectivity from ECS task

**Form Validation Errors**
- Check CSRF token generation
- Verify form field names match template
- Validate input length constraints

### Debug Commands
```bash
# Check ECS logs
aws logs tail /aws/ecs/myapp-ecs-logs --follow

# Test database connectivity
psql -h <rds-endpoint> -U appuser -d myapp_db

# Validate secret content
aws secretsmanager get-secret-value --secret-id myapp-dev-db-secret
```

---

**Last Updated**: September 2025  
**Python Version**: 3.8+  
**Flask Version**: 2.x  
**Database**: PostgreSQL 11+
