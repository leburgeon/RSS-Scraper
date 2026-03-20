# 1. Data Sources
data "aws_caller_identity" "current" {}

# 2. IAM Role for the Mock Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "c22_rag_chatbot_lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Attach basic execution policy so the Lambda can write logs to CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# 3. Create the Mock Python Lambda Code Dynamically
data "archive_file" "mock_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/mock_lambda.zip"
  source {
    content  = <<-EOF
      import json

      def lambda_handler(event, context):
          # In a real scenario, you would parse event.get('body') here
          return {
              "statusCode": 200,
              "headers": {
                  "Content-Type": "application/json"
              },
              "body": json.dumps({
                  "response": "This is a static mock response from the c22 RAG Lambda!"
              })
          }
    EOF
    filename = "main.py"
  }
}

# 4. The Placeholder Lambda Function
resource "aws_lambda_function" "rag_mock_lambda" {
  function_name    = "c22-rag-chatbot-lambda-ph"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.mock_lambda_zip.output_path
  source_code_hash = data.archive_file.mock_lambda_zip.output_base64sha256
}

# 5. API Gateway (HTTP API)
resource "aws_apigatewayv2_api" "rag_api" {
  name          = "c22-rag-chatbot-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"] # Consider restricting this to your Streamlit URL later
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["content-type", "authorization"]
    max_age       = 300
  }
}

# 6. API Gateway to Lambda Integration
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.rag_api.id
  integration_type       = "AWS_PROXY" # AWS_PROXY is the standard for Payload 2.0
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.rag_mock_lambda.invoke_arn
  payload_format_version = "2.0"
}

# 7. API Gateway Route (POST /chat)
resource "aws_apigatewayv2_route" "chat_route" {
  api_id    = aws_apigatewayv2_api.rag_api.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# 8. API Gateway Stage (Deploys the API)
resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.rag_api.id
  name        = "$default"
  auto_deploy = true
}

# 9. Permission for API Gateway to invoke the Lambda
resource "aws_lambda_permission" "api_gw_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rag_mock_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  # Restrict invocation to this specific API Gateway
  source_arn    = "${aws_apigatewayv2_api.rag_api.execution_arn}/*/*"
}

# 10. Output the final URL for Streamlit
output "chatbot_api_url" {
  description = "The URL to plug into your Streamlit frontend"
  value       = "${aws_apigatewayv2_stage.default_stage.invoke_url}chat"
}