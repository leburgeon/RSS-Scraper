# ECR

resource "aws_ecr_repository" "report_repo" {
  name                 = "rss-report-lambda-repo"
  image_tag_mutability = "MUTABLE"
}


# IAM ROLE FOR LAMBDA

resource "aws_iam_role" "lambda_role" {
  name = "rss-report-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution_report" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_custom_policy" {
  name = "rss-report-lambda-custom-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowDynamoRead"
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:BatchGetItem",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          "arn:aws:dynamodb:eu-west-2:129033205317:table/c22-rss-scraper-table"
        ]
      },
      {
        Sid    = "AllowSESSend"
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      },
      {
        Sid    = "AllowECRAuth"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Sid    = "AllowECRPull"
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = aws_ecr_repository.report_repo.arn
      },
      {
        Sid    = "AllowVPCNetworkInterface"
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_custom_policy_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_custom_policy.arn
}


# CLOUDWATCH LOG GROUP
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "rss-report-lambda-logs"
  retention_in_days = 14
}


# IAM ROLE FOR EVENTBRIDGE SCHEDULER

resource "aws_iam_role" "scheduler_role" {
  name = "rss-report-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "scheduler_invoke_lambda" {
  name = "rss-report-scheduler-invoke-lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.daily_report.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "scheduler_invoke_lambda_attach" {
  role       = aws_iam_role.scheduler_role.name
  policy_arn = aws_iam_policy.scheduler_invoke_lambda.arn
}


# EVENTBRIDGE SCHEDULER


resource "aws_scheduler_schedule" "daily_report_schedule" {
  name       = "rss-report-daily-report-7am"
  group_name = "default"

  schedule_expression          = "cron(*/5 * * * ? *)"
  schedule_expression_timezone = "Europe/London"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.daily_report.arn
    role_arn = aws_iam_role.scheduler_role.arn

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 2
    }
  }
}

# LAMBDA

resource "aws_lambda_function" "daily_report" {
  function_name = "rss-report-daily-lambda"
  role          = aws_iam_role.lambda_role.arn

  package_type = "Image"
  image_uri    = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/rss-report-lambda-repo:latest"
  architectures = ["x86_64"]
  timeout     = 300
  memory_size = 512



  environment {
    variables = {
      TABLE_NAME      = "c22-rss-scraper-table"
      SENDER_EMAIL      = "trainee.danish.handa@sigmalabs.co.uk"
      RECIPIENT_EMAIL   = "trainee.danish.handa@sigmalabs.co.uk"
      REPORT_NUM_DAYS = "2"
      REGION_NAME     = "eu-west-2"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
    aws_iam_role_policy_attachment.lambda_basic_execution_report,
    aws_iam_role_policy_attachment.lambda_custom_policy_attach
  ]
}
