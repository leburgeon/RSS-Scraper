variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "llm_api_key" {
  description = "API key for the LLM service"
  type        = string
  sensitive   = true
}

# ECR Repository Variables
variable "rag_ecr_repo_name" {
  description = "Name of the ECR repository for RAG Lambda"
  type        = string
  default     = "c22-rag-chatbot-lambda-repo"
}

# Lambda Variables
variable "rag_lambda_function_name" {
  description = "Name of the RAG Lambda function"
  type        = string
  default     = "c22-rag-chatbot-lambda"
}

variable "rag_lambda_role_name" {
  description = "Name of the Lambda execution role"
  type        = string
  default     = "c22-rag-chatbot-lambda-role"
}

variable "rag_lambda_secrets_policy_name" {
  description = "Name of the Lambda secrets access policy"
  type        = string
  default     = "c22-rag-lambda-secrets-policy"
}

variable "rag_lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "rag_lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 1024
}

variable "rag_lambda_sg_name" {
  description = "Security group name for Lambda"
  type        = string
  default     = "c22-rag-lambda-sg"
}

# API Gateway Variables
variable "rag_api_name" {
  description = "Name of the API Gateway"
  type        = string
  default     = "c22-rag-chatbot-api"
}

variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "$default"
}

variable "api_cors_allowed_origins" {
  description = "List of allowed origins for CORS"
  type        = list(string)
  default     = ["https://example.com"]
}

variable "api_burst_limit" {
  description = "API Gateway burst limit (requests per second)"
  type        = number
  default     = 5000
}

variable "api_rate_limit" {
  description = "API Gateway rate limit (requests per second, average)"
  type        = number
  default     = 2000
}

variable "api_logging_level" {
  description = "API Gateway logging level (ERROR, INFO, OFF)"
  type        = string
  default     = "INFO"
}

# Logging Variables
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}