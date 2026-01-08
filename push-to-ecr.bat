@echo off
setlocal

REM AWS ECR Push Script for Book Management Agent

REM Configuration
set AWS_REGION=eu-north-1
set AWS_ACCOUNT_ID=168034219342
set REPOSITORY_NAME=book-agent
set IMAGE_TAG=latest

echo === AWS ECR Push Script ===
echo Region: %AWS_REGION%
echo Account: %AWS_ACCOUNT_ID%
echo Repository: %REPOSITORY_NAME%
echo.

REM Step 1: Authenticate Docker to ECR
echo 1. Authenticating with AWS ECR...
for /f "tokens=*" %%i in ('aws ecr get-login-password --region %AWS_REGION%') do set ECR_PASSWORD=%%i
echo %ECR_PASSWORD% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com

if %ERRORLEVEL% NEQ 0 (
    echo ❌ ECR authentication failed!
    echo Make sure:
    echo - AWS CLI is installed and configured
    echo - You have ECR permissions
    echo - AWS credentials are set
    pause
    exit /b 1
)

echo ✅ ECR authentication successful

REM Step 2: Build the image
echo.
echo 2. Building Docker image...
docker build -f Dockerfile.minimal -t %REPOSITORY_NAME%:%IMAGE_TAG% .

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker build failed!
    pause
    exit /b 1
)

echo ✅ Docker build successful

REM Step 3: Tag the image
echo.
echo 3. Tagging image for ECR...
docker tag %REPOSITORY_NAME%:%IMAGE_TAG% %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%REPOSITORY_NAME%:%IMAGE_TAG%

echo ✅ Image tagged

REM Step 4: Push to ECR
echo.
echo 4. Pushing to ECR...
docker push %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%REPOSITORY_NAME%:%IMAGE_TAG%

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Push failed!
    pause
    exit /b 1
)

echo.
echo 🎉 Successfully pushed to ECR!
echo Image URI: %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%REPOSITORY_NAME%:%IMAGE_TAG%
pause