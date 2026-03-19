# Creates an Elastic Container Registry (ECR) to store the scraper's Docker images
resource "aws_ecr_repository" "c22_rss_scraper_repository" {
  name                 = "c22_rss_scraper_repository"
  image_tag_mutability = "MUTABLE"
}

# Creates a DynamoDB table to store the parsed RSS feed items
resource "aws_dynamodb_table" "c22_rss_scraper_table" {
  name         = "c22_rss_scraper_table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
}

# Creates an ECS Cluster, acting as a logical grouping for the Fargate tasks
resource "aws_ecs_cluster" "c22_rss_scraper_cluster" {
  name = "c22_rss_scraper_cluster"
}

# Creates a CloudWatch log group with a 14-day retention to store scraper logs
resource "aws_cloudwatch_log_group" "c22_rss_scraper_log_group" {
  name              = "c22_rss_scraper_log_group"
  retention_in_days = 14
}

# Defines a security group allowing the scraper task to reach the internet (HTTPS port 443)
resource "aws_security_group" "c22_rss_scraper_sg" {
  name        = "c22_rss_scraper_security_group"
  description = "Allow outbound HTTPS for RSS scraping"
  vpc_id      = data.aws_vpc.c22_vpc.id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Creates the IAM role assumed by the ECS task to pull images, log, and access DynamoDB
resource "aws_iam_role" "c22_rss_scraper_role" {
  name = "c22_rss_scraper_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

# Attaches the AWS-managed policy allowing the ECS task to pull from ECR and write to CloudWatch
resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.c22_rss_scraper_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Creates a custom IAM policy granting the scraper permission to read/write to the DynamoDB table
resource "aws_iam_policy" "c22_rss_scraper_policy" {
  name = "c22_rss_scraper_policy"
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

# Defines the ECS task blueprint, including CPU, memory, Docker image, and log routing
resource "aws_ecs_task_definition" "c22_rss_scraper_task_definition" {
  family                   = "c22_rss_scraper_task_definition"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.c22_rss_scraper_role.arn
  task_role_arn            = aws_iam_role.c22_rss_scraper_role.arn

  container_definitions = jsonencode([{
    name      = "c22_rss_scraper_container"
    image     = "${aws_ecr_repository.c22_rss_scraper_repository.repository_url}:latest"
    essential = true
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.c22_rss_scraper_log_group.name
        "awslogs-region"        = data.aws_region.current.name
        "awslogs-stream-prefix" = "c22_rss_scraper"
      }
    }
  }])
}

# Creates the IAM role assumed by the EventBridge Scheduler to trigger the task
resource "aws_iam_role" "c22_rss_scraper_scheduler_role" {
  name = "c22_rss_scraper_scheduler_role"
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
  name = "c22_rss_scraper_scheduler_policy"
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
  name                = "c22_rss_scraper_schedule"
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