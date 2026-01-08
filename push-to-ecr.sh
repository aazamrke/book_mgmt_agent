#!/bin/bash

# AWS ECR Push Script for Book Management Agent

# Configuration
AWS_REGION="eu-north-1"
AWS_ACCOUNT_ID="168034219342"
REPOSITORY_NAME="book-agent"
IMAGE_TAG="latest"

echo "=== AWS ECR Push Script ==="
echo "Region: $AWS_REGION"
echo "Account: $AWS_ACCOUNT_ID"
echo "Repository: $REPOSITORY_NAME"
echo ""

# Step 1: Authenticate Docker to ECR
echo "1. Authenticating with AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

if [ $? -ne 0 ]; then
    echo "❌ ECR authentication failed!"
    echo "Make sure:"
    echo "- AWS CLI is installed and configured"
    echo "- You have ECR permissions"
    echo "- AWS credentials are set"
    exit 1
fi

echo "✅ ECR authentication successful"

# Step 2: Build the image
echo ""
echo "2. Building Docker image..."
docker build -f Dockerfile.minimal -t $REPOSITORY_NAME:$IMAGE_TAG .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker build successful"

# Step 3: Tag the image
echo ""
echo "3. Tagging image for ECR..."
docker tag $REPOSITORY_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG

echo "✅ Image tagged"

# Step 4: Push to ECR
echo ""
echo "4. Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG

if [ $? -ne 0 ]; then
    echo "❌ Push failed!"
    exit 1
fi

echo ""
echo "🎉 Successfully pushed to ECR!"
echo "Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG"