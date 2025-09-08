provider "aws" {
  region = "ap-south-1"
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "tf_state_file_smd" {
  bucket = "my-terraform-state-smd29-py"

  # Updated versioning block
  versioning {
    enabled = true
  }

  # Updated encryption block
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    Name        = "Terraform State Bucket"
    Environment = "Shared"
  }
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "tf_lock" {
  name         = "terraform-lock-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform Lock Table"
    Environment = "Shared"
  }
}
