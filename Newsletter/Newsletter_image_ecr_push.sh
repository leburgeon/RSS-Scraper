# set -e

# AWS_REGION="eu-west-2"
# AWS_ACCOUNT_ID="129033205317"
# ECR_REPOSITORY_NAME="rss-report-lambda-repo"
# IMAGE_TAG="latest"

# ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"

# echo "Logging in to Amazon ECR..."
# aws ecr get-login-password --region "${AWS_REGION}" | \
# docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# echo "Building and pushing Lambda-compatible image..."
# docker buildx build \
#   --platform linux/amd64 \
#   --provenance=false \
#   -t "${ECR_URI}" \
#   --push .

# aws lambda update-function-code \
#   --function-name rss-report-daily-lambda \
#   --image-uri 129033205317.dkr.ecr.eu-west-2.amazonaws.com/rss-report-lambda-repo:latest


set -e

AWS_REGION="eu-west-2"
AWS_ACCOUNT_ID="129033205317"
ECR_REPOSITORY_NAME="rss-report-lambda-repo"
IMAGE_TAG="latest"
LAMBDA_FUNCTION_NAME="rss-report-daily-lambda"

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"

echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building and pushing Lambda-compatible image..."
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  -t "${ECR_URI}" \
  --push .

echo "Updating Lambda to use latest image..."
aws lambda update-function-code \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --image-uri "${ECR_URI}" \
  --region "${AWS_REGION}"

echo "Done. Lambda now points to ${ECR_URI}"