#!/bin/bash

# Exit immediately if any command fails
set -e

# Define your specific AWS variables
REGION="eu-west-2"
ACCOUNT_ID="129033205317"
REPO_NAME="c22-rag-chatbot-lambda-repo"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "🔐 Logging into AWS ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_UqRI

echo "🏗️  Building the Docker image (forcing amd64 architecture for AWS Lambda)..."
docker build --platform linux/amd64 --provenance=false -t $REPO_NAME .

echo "🏷️  Tagging the image for ECR..."
docker tag $REPO_NAME:latest $ECR_URI/$REPO_NAME:latest

echo "🚀 Pushing the image to ECR..."
docker push $ECR_URI/$REPO_NAME:latest

echo "✅ Successfully pushed to $ECR_URI/$REPO_NAME:latest!"

echo "🔄 Forcing Lambda to update to the new image..."
aws lambda update-function-code \
  --function-name c22-rag-chatbot-lambda \
  --image-uri $ECR_URI/$REPO_NAME:latest

echo "✅ Lambda update initiated!"