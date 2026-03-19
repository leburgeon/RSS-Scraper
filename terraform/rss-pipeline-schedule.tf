# 1. NETWORKING: Security Group with Egress
resource "aws_security_group" "c22_rss_scraper_sg" {
  name        = "c22_rss_scraper_sg"
  description = "Allow outbound HTTPS for RSS scraping"
  vpc_id      = data.aws_vpc.c22_vpc.id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. IAM: Execution Role (Infrastructure level - ECR & Logs)
resource "aws_iam_role" "ecs_execution_role" {
  name = "c22_rss_scraper_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_standard" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 3. IAM: Task Role (Application level - DynamoDB access)
resource "aws_iam_role" "rss_task_role" {
  name = "c22_rss_scraper_task_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" } }]
  })
}

resource "aws_iam_policy" "dynamodb_access" {
  name = "c22_rss_scraper_dynamo_policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = ["dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:GetItem", "dynamodb:Scan", "dynamodb:Query"]
      Effect   = "Allow"
      Resource = aws_dynamodb_table.c22_rss_scraper_table.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_role_attach" {
  role       = aws_iam_role.rss_task_role.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}

# 4. ECS: Task Definition with Logging
resource "aws_cloudwatch_log_group" "c22_rss_scraper_log_group" {
  name              = "c22_rss_scraper_log_group"
  retention_in_days = 14
}

resource "aws_ecs_task_definition" "c22_rss_scraper_task" {
  family                   = "c22_rss_scraper_task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.rss_task_role.arn

  container_definitions = jsonencode([{
    name      = "scraper"
    image     = "${aws_ecr_repository.c22_rss_scraper_repository.repository_url}:latest"
    essential = true
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.c22_rss_scraper_log_group.name
        "awslogs-region"        = data.aws_region.current.name
        "awslogs-stream-prefix" = "rss-scraper"
      }
    }
  }])
}

# 5. SCHEDULER: The "Brain" that triggers the task
resource "aws_scheduler_schedule" "c22_rss_scraper_schedule" {
  name = "c22_rss_scraper_schedule"
  schedule_expression = "rate(1 hour)"

  flexible_time_window { mode = "OFF" }

  target {
    arn      = aws_ecs_cluster.c22_rss_scraper_cluster.arn
    role_arn = aws_iam_role.c22_rss_scraper_scheduler_role.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.c22_rss_scraper_task.arn
      launch_type         = "FARGATE"
      network_configuration {
        subnets          = data.aws_subnets.public_subnets.ids
        security_groups  = [aws_security_group.c22_rss_scraper_sg.id]
        assign_public_ip = true
      }
    }
  }
}