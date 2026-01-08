# ECR Permission Fix Guide

## Problem
User `sagemaker_user` doesn't have ECR permissions to push Docker images.

## Solutions

### Option 1: Add ECR Permissions to IAM User

1. **Go to AWS IAM Console**
   - Navigate to IAM > Users > sagemaker_user

2. **Attach ECR Policy**
   - Click "Add permissions" > "Attach existing policies directly"
   - Search for "AmazonEC2ContainerRegistryPowerUser"
   - Or create custom policy using `ecr-policy.json`

3. **Create ECR Repository** (if not exists)
   ```bash
   aws ecr create-repository --repository-name book-agent --region eu-north-1
   ```

### Option 2: Use Docker Hub Instead

1. **Create Docker Hub account** at https://hub.docker.com
2. **Update script** with your username in `push-to-dockerhub.bat`
3. **Run the script**:
   ```bash
   push-to-dockerhub.bat
   ```

### Option 3: Use Different AWS User

1. **Create new IAM user** with ECR permissions
2. **Configure AWS CLI** with new credentials:
   ```bash
   aws configure
   ```

## Quick Commands

### For ECR (after fixing permissions):
```bash
# Create repository
aws ecr create-repository --repository-name book-agent --region eu-north-1

# Run push script
push-to-ecr.bat
```

### For Docker Hub:
```bash
# Edit username in script first
push-to-dockerhub.bat
```

## IAM Policy Required
The user needs these ECR permissions:
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`