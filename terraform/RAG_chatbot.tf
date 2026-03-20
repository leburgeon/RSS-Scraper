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

output "repository_url" {
  value = aws_ecr_repository.c22_media_group_chatbot_frontend.repository_url
  description = "The URL to use in your Docker push and ECS Task Definition"
}