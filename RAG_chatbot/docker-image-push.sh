#!/bin/bash

# Exit immediately if any command fails
set -e

# Define your specific AWS variables
REGION="eu-west-2"
ACCOUNT_ID="129033205317"
REPO_NAME="c22-rag-chatbot-lambda-repo"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "🔐 Logging into AWS ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

echo "🏗️  Building the Docker image (forcing amd64 architecture and disabling provenance)..."
docker build --platform linux/amd64 --provenance=false -t $REPO_NAME .

echo "🏷️  Tagging the image for ECR..."
docker tag $REPO_NAME:latest $ECR_URI/$REPO_NAME:latest

echo "🚀 Pushing the image to ECR..."
docker push $ECR_URI/$REPO_NAME:latest
echo "✅ Successfully pushed to ECR!"

echo "🔄 Forcing Lambda to update to the new image..."
# Note: If you haven't successfully run 'terraform apply' yet, this next command will fail 
# because the Lambda doesn't exist. That's okay! Just run terraform apply, and next time 
# you run this script, it will update perfectly.
aws lambda update-function-code \
  --function-name c22-rag-chatbot-lambda \
  --image-uri $ECR_URI/$REPO_NAME:latest > /dev/null

echo "✅ Lambda update initiated! You are good to go."