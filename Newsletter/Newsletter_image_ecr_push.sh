set -e

AWS_REGION="eu-west-2"
AWS_ACCOUNT_ID="129033205317"
ECR_REPOSITORY_NAME="rss-report-lambda-repo"
IMAGE_TAG="latest"
LOCAL_IMAGE_NAME="rss-report-lambda"

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

echo "Starting Docker build and push process..."
echo "AWS Region: ${AWS_REGION}"
echo "ECR Repository: ${ECR_URI}"
echo "Local Image Name: ${LOCAL_IMAGE_NAME}"


# LOGIN TO ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"


# BUILD IMAGE
echo "Building Docker image..."
docker build --platform linux/amd64 -t "${LOCAL_IMAGE_NAME}:${IMAGE_TAG}" .


# TAG IMAGE
echo "Tagging Docker image..."
docker tag "${LOCAL_IMAGE_NAME}:${IMAGE_TAG}" "${ECR_URI}:${IMAGE_TAG}"

# PUSH IMAGE
echo "Pushing Docker image to ECR..."
docker push "${ECR_URI}:${IMAGE_TAG}"

echo "Done."
echo "Image pushed to: ${ECR_URI}:${IMAGE_TAG}"