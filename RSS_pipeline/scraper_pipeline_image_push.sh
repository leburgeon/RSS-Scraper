#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define variables
REGION="eu-west-2"
REPO_NAME="c22-rss-scraper-repository"

echo "Fetching AWS Account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "Logging into AWS ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

echo "Building the Docker image (forcing amd64 architecture for AWS Fargate)..."
docker build --platform linux/amd64 -t $REPO_NAME .

echo "Tagging the image for ECR..."
docker tag $REPO_NAME:latest $ECR_URI/$REPO_NAME:latest

echo "Pushing the image to ECR..."
docker push $ECR_URI/$REPO_NAME:latest

echo "✅ Successfully pushed to $ECR_URI/$REPO_NAME:latest"