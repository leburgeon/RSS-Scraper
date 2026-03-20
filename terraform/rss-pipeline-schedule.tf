# Creates an Elastic Container Registry (ECR) to store the scraper's Docker images
resource "aws_ecr_repository" "c22_rss_scraper_repository" {
  name                 = "c22-rss-scraper-repository"
  image_tag_mutability = "MUTABLE"
}

# Creates a DynamoDB table to store the parsed RSS feed items
resource "aws_dynamodb_table" "c22_rss_scraper_table" {
  name         = "c22-rss-scraper-table"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "PK"
  range_key = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }
}

# Creates an ECS Cluster, acting as a logical grouping for the Fargate tasks
resource "aws_ecs_cluster" "c22_rss_scraper_cluster" {
  name = "c22-rss-scraper-cluster"
}

# Creates a CloudWatch log group with a 14-day retention to store scraper logs
resource "aws_cloudwatch_log_group" "c22_rss_scraper_log_group" {
  name              = "c22-rss-scraper-log-group"
  retention_in_days = 14
}

# Defines a security group allowing the scraper task to reach the internet (HTTPS port 443)
resource "aws_security_group" "c22_rss_scraper_sg" {
  name        = "c22-rss-scraper-security-group"
  description = "Allow outbound HTTPS for RSS scraping"
  vpc_id      = data.aws_vpc.c22_vpc.id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

}

# Allow RSS scraper ECS task to connect to RDS
resource "aws_security_group_rule" "rss_scraper_to_rds_egress" {
  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.rds.id
  security_group_id        = aws_security_group.c22_rss_scraper_sg.id
  description              = "Allow RSS scraper ECS task to connect to RDS"
}

# Allow DNS resolution (required for RDS hostname lookup)
resource "aws_security_group_rule" "rss_scraper_dns_egress" {
  type              = "egress"
  from_port         = 53
  to_port           = 53
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.c22_rss_scraper_sg.id
  description       = "Allow DNS queries for hostname resolution"
}

# Creates the IAM role assumed by the ECS task definition to pull images, log, and access DynamoDB
resource "aws_iam_role" "c22_rss_scraper_role" {
  name = "c22-rss-scraper-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

# Creates a custom IAM policy granting the scraper permission to read secrets from Secrets Manager
resource "aws_iam_role_policy" "task-execution-role-policy" {
  name = "task-execution-role-policy"
  role = aws_iam_role.c22_rss_scraper_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          aws_secretsmanager_secret.db_credentials.arn,
          aws_secretsmanager_secret.llm_api_key.arn
        ]
      }
    ]
  })
}

# Attaches the AWS-managed policy allowing the ECS task to pull from ECR and write to CloudWatch
resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.c22_rss_scraper_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Creates a custom IAM policy granting the scraper permission to read/write to the DynamoDB table
resource "aws_iam_policy" "c22_rss_scraper_policy" {
  name = "c22-rss-scraper-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:GetItem", "dynamodb:Scan", "dynamodb:Query"]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.c22_rss_scraper_table.arn
      }
    ]
  })
}

# Attaches the custom DynamoDB policy to the scraper's IAM role
resource "aws_iam_role_policy_attachment" "c22_rss_scraper_custom_attach" {
  role       = aws_iam_role.c22_rss_scraper_role.name
  policy_arn = aws_iam_policy.c22_rss_scraper_policy.arn
}

# Creates the secrets manager secret to store the LLM API key
resource "aws_secretsmanager_secret" "llm_api_key" {
  name        = "c22-rss-scraper-llm-api-key"
  description = "API key for the LLM service used by the RSS scraper"
}

# Attaches the LLM API key value to the Secrets Manager secret
resource "aws_secretsmanager_secret_version" "llm_api_key_version" {
  secret_id     = aws_secretsmanager_secret.llm_api_key.id
  secret_string = var.llm_api_key

  lifecycle {
    ignore_changes = [ secret_string ]
  }
}

# Creates the secrets manager secret to store the RDS database credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "c22-rss-scraper-db-credentials"
  description = "RDS database credentials for the RSS scraper"
}

# In rss-pipeline-schedule.tf
resource "aws_secretsmanager_secret_version" "db_credentials_version" {
  secret_id     = aws_secretsmanager_secret.db_credentials.id
  secret_string = random_password.rds_master_password.result  # Just the password
}

# Defines the ECS task blueprint, including CPU, memory, Docker image, and log routing
resource "aws_ecs_task_definition" "c22_rss_scraper_task_definition" {
  family                   = "c22-rss-scraper-task-definition"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.c22_rss_scraper_role.arn
  task_role_arn            = aws_iam_role.c22_rss_scraper_role.arn

  container_definitions = jsonencode([{
    name      = "c22-rss-scraper-container"
    image     = "${aws_ecr_repository.c22_rss_scraper_repository.repository_url}:latest"
    essential = true
    secrets = [
      {
        name      = "OPENAI_API_KEY"
        valueFrom = aws_secretsmanager_secret.llm_api_key.arn
      },
      {
      name      = "RDS_PASSWORD"
        valueFrom = aws_secretsmanager_secret.db_credentials.arn
      }
    ]
    environment = [
      {
        name  = "TABLE_NAME"
        value = aws_dynamodb_table.c22_rss_scraper_table.name
      },
      {
        name  = "AWS_REGION"
        value = data.aws_region.current.name
      },
      {
        name  = "RDS_HOST"
        value = aws_db_instance.rag_db.address
      },
      {
        name  = "RDS_PORT"
        value = "5432"
      },
      {
        name  = "RDS_DB_NAME"
        value = "rag_database"
      },
      {
        name  = "RDS_USER"
        value = "media_group_project_RAG_DB"
      }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.c22_rss_scraper_log_group.name
        "awslogs-region"        = data.aws_region.current.name
        "awslogs-stream-prefix" = "c22-rss-scraper"
      }
    }
  }])
}

# Creates the IAM role assumed by the EventBridge Scheduler to trigger the task
resource "aws_iam_role" "c22_rss_scraper_scheduler_role" {
  name = "c22-rss-scraper-scheduler-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

# Creates a policy allowing the Scheduler to run the ECS task and pass the required IAM roles
resource "aws_iam_policy" "c22_rss_scraper_scheduler_policy" {
  name = "c22-rss-scraper-scheduler-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "ecs:RunTask"
        Effect   = "Allow"
        Resource = aws_ecs_task_definition.c22_rss_scraper_task_definition.arn
      },
      {
        Action   = "iam:PassRole"
        Effect   = "Allow"
        Resource = aws_iam_role.c22_rss_scraper_role.arn
      }
    ]
  })
}

# Attaches the Scheduler policy to the Scheduler IAM role
resource "aws_iam_role_policy_attachment" "c22_rss_scraper_scheduler_attach" {
  role       = aws_iam_role.c22_rss_scraper_scheduler_role.name
  policy_arn = aws_iam_policy.c22_rss_scraper_scheduler_policy.arn
}

# Creates an EventBridge Schedule to trigger the ECS Fargate task every hour
resource "aws_scheduler_schedule" "c22_rss_scraper_schedule" {
  name                = "c22-rss-scraper-schedule"
  schedule_expression = "rate(1 hour)"

  flexible_time_window { mode = "OFF" }

  target {
    arn      = aws_ecs_cluster.c22_rss_scraper_cluster.arn
    role_arn = aws_iam_role.c22_rss_scraper_scheduler_role.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.c22_rss_scraper_task_definition.arn
      launch_type         = "FARGATE"
      network_configuration {
        subnets          = data.aws_subnets.public_subnets.ids
        security_groups  = [aws_security_group.c22_rss_scraper_sg.id]
        assign_public_ip = true
      }
    }
  }
}