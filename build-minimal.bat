@echo off
echo Building minimal Docker image (target: <1GB)...

REM Build minimal image
docker build -f Dockerfile.minimal -t book-mgmt-minimal .

if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo Checking image size...
docker images book-mgmt-minimal

echo.
echo Minimal image built successfully!
echo Run with: docker run -p 8000:8000 book-mgmt-minimal
echo.
echo Note: This version has:
echo - No ML dependencies (sentence-transformers, numpy, etc.)
echo - Simple text-based search instead of semantic search
echo - Basic summary generation without AI
echo - Alpine Linux base (much smaller)
echo.
pause