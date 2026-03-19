data "aws_subnets" "c22_private" {
  filter {
    name   = "tag:Name"
    values = ["c22-private-subnet-1", "c22-private-subnet-2", "c22-private-subnet-3"]
  }
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.c22_vpc.id]
  }
}

data "aws_security_group" "rss_scraper" {
  name   = "c22-rss-scraper-security-group"
  vpc_id = data.aws_vpc.c22_vpc.id
}

# Security group for Lambda
resource "aws_security_group" "lambda_rds" {
  name        = "c22-lambda-rds-security-group"
  description = "Security group for Lambda to access RDS"
  vpc_id      = data.aws_vpc.c22_vpc.id

  tags = {
    Name = "c22-lambda-rds-security-group"
  }
}

# Security group for RDS
resource "aws_security_group" "rds" {
  name        = "c22-rag-rds-security-group"
  description = "Security group for RAG RDS database"
  vpc_id      = data.aws_vpc.c22_vpc.id

  tags = {
    Name = "c22-rag-rds-security-group"
  }
}

# Security group rules
resource "aws_security_group_rule" "lambda_to_rds_egress" {
  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.rds.id
  security_group_id        = aws_security_group.lambda_rds.id
  description              = "Allow Lambda to connect to RDS"
}

resource "aws_security_group_rule" "rss_scraper_to_rds_ingress" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = data.aws_security_group.rss_scraper.id
  security_group_id        = aws_security_group.rds.id
  description              = "Allow RSS scraper ECS task to connect to RDS"
}

resource "aws_security_group_rule" "lambda_to_rds_ingress" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.lambda_rds.id
  security_group_id        = aws_security_group.rds.id
  description              = "Allow Lambda to connect to RDS"
}

# DB subnet group
resource "aws_db_subnet_group" "rag_db_subnet_group" {
  name       = "c22-rag-db-subnet-group"
  subnet_ids = data.aws_subnets.c22_private.ids

  tags = {
    Name = "c22-rag-db-subnet-group"
  }
}

# Random password for RDS master user
resource "random_password" "rds_master_password" {
  length  = 32
  special = true
}

# Store password in Secrets Manager
resource "aws_secretsmanager_secret" "rds_master_password" {
  name                    = "c22-rag-db-master-password"
  recovery_window_in_days = 7

  tags = {
    Name = "c22-rag-db-master-password"
  }
}

resource "aws_secretsmanager_secret_version" "rds_master_password" {
  secret_id = aws_secretsmanager_secret.rds_master_password.id
  secret_string = jsonencode({
    username = "media_group_project_RAG_DB"
    password = random_password.rds_master_password.result
    engine   = "postgres"
    host     = aws_db_instance.rag_db.address
    port     = 5432
    dbname   = "rag_database"
  })
}

# RDS PostgreSQL instance
resource "aws_db_instance" "rag_db" {
  identifier              = "c22-media-rag-db"
  engine                  = "postgres"
  engine_version          = "15"
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  storage_type            = "gp3"
  db_name                 = "rag_database"
  username                = "media_group_project_RAG_DB"
  password                = random_password.rds_master_password.result
  db_subnet_group_name    = aws_db_subnet_group.rag_db_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  publicly_accessible     = false
  skip_final_snapshot     = true
  multi_az                = false

  tags = {
    Name = "c22-media-rag-db"
  }
}

# Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.rag_db.endpoint
}

output "rds_address" {
  description = "RDS instance address (hostname only)"
  value       = aws_db_instance.rag_db.address
}

output "secrets_manager_arn" {
  description = "ARN of the Secrets Manager secret containing RDS credentials"
  value       = aws_secretsmanager_secret.rds_master_password.arn
}

output "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  value       = aws_security_group.lambda_rds.id
}