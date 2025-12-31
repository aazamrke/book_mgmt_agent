@echo off
echo Building Docker image...

REM Try simple build without pull flag
docker build -t book-mgmt-agent .

if %ERRORLEVEL% NEQ 0 (
    echo Docker build failed. Trying alternative approach...
    
    REM Try without cache
    docker build --no-cache -t book-mgmt-agent .
    
    if %ERRORLEVEL% NEQ 0 (
        echo Docker build still failing. Please check:
        echo 1. Docker Desktop is running
        echo 2. Internet connection is available
        echo 3. Try restarting Docker Desktop
        echo.
        echo Alternative: Run locally with:
        echo pip install -r requirements.txt
        echo uvicorn app.main:app --reload --port 8000
        pause
        exit /b 1
    )
)

echo Build successful!
echo Run with: docker run -p 8000:8000 book-mgmt-agent
pause