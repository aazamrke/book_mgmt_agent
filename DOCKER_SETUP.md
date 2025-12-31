# Docker Setup Troubleshooting

## Error: Docker Desktop not running

The error `//./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified` means Docker Desktop is not running.

### Solution:

1. **Start Docker Desktop**
   - Open Docker Desktop application
   - Wait for it to fully start (green icon in system tray)
   - Ensure Docker engine is running

2. **Verify Docker is running**
   ```bash
   docker --version
   docker ps
   ```

3. **Alternative: Use Docker without Desktop**
   If you don't have Docker Desktop, install Docker Engine directly or use these alternatives:

### Quick Build Commands:

```bash
# Build the image
docker build -t book-mgmt-agent .

# Run with docker-compose
docker-compose up -d

# Or run manually
docker run -p 8000:8000 book-mgmt-agent
```

### Manual Setup (without Docker):

If Docker issues persist, run locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
set DB_HOST=localhost
set DB_NAME=book_mgmt
set USE_S3=false

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Desktop Installation:

Download from: https://www.docker.com/products/docker-desktop/

After installation:
1. Start Docker Desktop
2. Wait for initialization
3. Try building again