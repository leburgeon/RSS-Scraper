# --- 1. ECR REPOSITORY & LIFECYCLE POLICY ---

resource "aws_ecr_repository" "c22_media_group_chatbot_frontend" {
  name                 = "c22_media_group_chatbot_frontend"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
  }

  tags = {
    Environment = "Dev"
    Project     = "Chatbot"
  }
}

resource "aws_ecr_lifecycle_policy" "cleanup_policy" {
  repository = aws_ecr_repository.c22_media_group_chatbot_frontend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the last 5 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 5
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# --- 2. NETWORK DATA SOURCES ---

data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = ["c22-VPC"]
  }
}

data "aws_subnets" "public" {
  filter {
    name   = "tag:Name"
    values = ["c22-public-subnet-*"]
  }
}

# --- 3. SECURITY GROUP ---

resource "aws_security_group" "streamlit_sg" {
  name        = "c22-chatbot-frontend-sg"
  description = "Allow Streamlit 8501 and outbound API Gateway access"
  vpc_id      = data.aws_vpc.selected.id

  ingress {
    description = "Streamlit UI Access"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "HTTPS to API Gateway"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "DNS Resolution"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "c22-chatbot-sg"
    Project = "Chatbot"
  }
}

# --- 4. IAM ROLES & LOGGING ---

resource "aws_cloudwatch_log_group" "chatbot_log_group" {
  name              = "/ecs/c22-chatbot-frontend"
  retention_in_days = 7
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "c22_chatbot_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# --- 5. ECS TASK & SERVICE ---

resource "aws_ecs_task_definition" "chatbot_task" {
  family                   = "c22-chatbot-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([{
    name      = "streamlit-app"
    image     = aws_ecr_repository.c22_media_group_chatbot_frontend.repository_url
    essential = true
    portMappings = [{
      containerPort = 8501
      hostPort      = 8501
      protocol      = "tcp"
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.chatbot_log_group.name
        "awslogs-region"        = "eu-west-2"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_ecs_service" "chatbot_service" {
  name            = "c22-chatbot-service"
  cluster         = "c22-rss-scraper-cluster"
  task_definition = aws_ecs_task_definition.chatbot_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.streamlit_sg.id]
    assign_public_ip = true
  }
}

# --- 6. OUTPUTS ---

output "repository_url" {
  value       = aws_ecr_repository.c22_media_group_chatbot_frontend.repository_url
  description = "The URL to use in your Docker push and ECS Task Definition"
}

output "streamlit_access_url" {
  description = "Wait for the ECS task to start, then use the Public IP of the task on port 8501"
  value       = "Check ECS Console for Task Public IP"
}