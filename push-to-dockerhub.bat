@echo off
setlocal

REM Docker Hub Push Script (Alternative to ECR)

REM Configuration
set DOCKER_USERNAME=your_dockerhub_username
set REPOSITORY_NAME=book-mgmt-agent
set IMAGE_TAG=latest

echo === Docker Hub Push Script ===
echo Username: %DOCKER_USERNAME%
echo Repository: %REPOSITORY_NAME%
echo.

REM Step 1: Login to Docker Hub
echo 1. Login to Docker Hub...
echo Please enter your Docker Hub password when prompted:
docker login --username %DOCKER_USERNAME%

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Hub login failed!
    pause
    exit /b 1
)

echo ✅ Docker Hub login successful

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

REM Step 3: Tag for Docker Hub
echo.
echo 3. Tagging image for Docker Hub...
docker tag %REPOSITORY_NAME%:%IMAGE_TAG% %DOCKER_USERNAME%/%REPOSITORY_NAME%:%IMAGE_TAG%

echo ✅ Image tagged

REM Step 4: Push to Docker Hub
echo.
echo 4. Pushing to Docker Hub...
docker push %DOCKER_USERNAME%/%REPOSITORY_NAME%:%IMAGE_TAG%

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Push failed!
    pause
    exit /b 1
)

echo.
echo 🎉 Successfully pushed to Docker Hub!
echo Image: %DOCKER_USERNAME%/%REPOSITORY_NAME%:%IMAGE_TAG%
echo Pull with: docker pull %DOCKER_USERNAME%/%REPOSITORY_NAME%:%IMAGE_TAG%
pause