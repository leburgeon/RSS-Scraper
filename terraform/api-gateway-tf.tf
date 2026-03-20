# ==========================================
# 1. LAMBDA CONTAINER & IAM
# ==========================================

resource "aws_ecr_repository" "rag_lambda_repo" {
  name                 = "c22-rag-chatbot-lambda-repo"
  image_tag_mutability = "MUTABLE"
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "c22-rag-chatbot-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_secrets_policy" {
  name        = "c22-rag-lambda-secrets-policy"
  description = "Allows Lambda to read RAG API key and DB creds"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = "secretsmanager:GetSecretValue"
      Effect   = "Allow"
      Resource = [
        aws_secretsmanager_secret.llm_api_key.arn,
        aws_secretsmanager_secret.db_credentials.arn
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_secrets_policy.arn
}

resource "aws_lambda_function" "rag_container_lambda" {
  function_name = "c22-rag-chatbot-lambda"
  role          = aws_iam_role.lambda_exec_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.rag_lambda_repo.repository_url}:latest"
  
  timeout       = 60 
  memory_size   = 1024 

  environment {
    variables = {
      # These reference resources in your other .tf files!
      LLM_API_KEY_SECRET_ARN = aws_secretsmanager_secret.llm_api_key.arn
      DB_CREDS_SECRET_ARN    = aws_secretsmanager_secret.db_credentials.arn
      DB_HOST                = aws_db_instance.rag_db.address
      DB_PORT                = tostring(aws_db_instance.rag_db.port)
      DB_NAME                = aws_db_instance.rag_db.db_name
    }
  }
}

# ==========================================
# 2. API GATEWAY
# ==========================================

resource "aws_apigatewayv2_api" "rag_api" {
  name          = "c22-rag-chatbot-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"] 
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["content-type", "authorization"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.rag_api.id
  integration_type       = "AWS_PROXY" 
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.rag_container_lambda.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "chat_route" {
  api_id    = aws_apigatewayv2_api.rag_api.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.rag_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gw_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rag_container_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.rag_api.execution_arn}/*/*"
}

output "chatbot_api_url" {
  description = "The URL to plug into your Streamlit frontend"
  value       = "${aws_apigatewayv2_stage.default_stage.invoke_url}chat"
}