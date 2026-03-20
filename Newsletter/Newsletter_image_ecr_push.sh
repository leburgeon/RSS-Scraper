set -e

#AWS and deployment settings
AWS_REGION="eu-west-2"
AWS_ACCOUNT_ID="129033205317"
ECR_REPOSITORY_NAME="rss-report-lambda-repo"
IMAGE_TAG="latest"
LAMBDA_FUNCTION_NAME="rss-report-daily-lambda"


#Full ECR URI for the image that docker will push to and Lambda will pull from
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"

#Login docker to ECR, build the image, push it to ECR, and update the Lambda function to use the new image
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

#Build a lambda compatible image for linux/amd64 and push to ECR
echo "Building and pushing Lambda-compatible image..."
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  -t "${ECR_URI}" \
  --push .

#Tell Lambda to use the new image from ECR
echo "Updating Lambda to use latest image..."
aws lambda update-function-code \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --image-uri "${ECR_URI}" \
  --region "${AWS_REGION}"

#Final confirmation message
echo "Done. Lambda now points to ${ECR_URI}"