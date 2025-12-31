#!/bin/bash

# Build and run the Book Management System with Docker

echo "Building Docker image..."
docker build -t book-mgmt-agent .

echo "Starting services with docker-compose..."
docker-compose up -d

echo "Waiting for database to be ready..."
sleep 10

echo "Creating database tables..."
docker-compose exec app python -c "
from app.database import engine, Base
from app.models import *
import asyncio

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Database tables created successfully')

asyncio.run(create_tables())
"

echo "Application is running at http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"