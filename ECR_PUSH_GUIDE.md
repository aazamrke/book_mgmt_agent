# AWS ECR Push Commands

## Prerequisites
1. Install AWS CLI: https://aws.amazon.com/cli/
2. Configure AWS credentials: `aws configure`
3. Ensure you have ECR permissions

## Manual Commands

### 1. Authenticate with ECR
```bash
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin 168034219342.dkr.ecr.eu-north-1.amazonaws.com
```

### 2. Build the image
```bash
docker build -f Dockerfile.minimal -t book-agent:latest .
```

### 3. Tag for ECR
```bash
docker tag book-agent:latest 168034219342.dkr.ecr.eu-north-1.amazonaws.com/book-agent:latest
```

### 4. Push to ECR
```bash
docker push 168034219342.dkr.ecr.eu-north-1.amazonaws.com/book-agent:latest
```

## Automated Scripts

### Windows
```bash
push-to-ecr.bat
```

### Linux/Mac
```bash
chmod +x push-to-ecr.sh
./push-to-ecr.sh
```

## Troubleshooting

### Error: "no basic auth credentials"
- Run the ECR login command first
- Check AWS credentials: `aws sts get-caller-identity`

### Error: "repository does not exist"
- Create ECR repository: `aws ecr create-repository --repository-name book-agent --region eu-north-1`

### Error: "access denied"
- Check IAM permissions for ECR
- Ensure you have `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`, `ecr:PutImage` permissions