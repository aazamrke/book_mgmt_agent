#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def main():
    try:
        from app.config import settings
        print(f"✓ Config loaded")
        print(f"  Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        print(f"  Environment: {settings.APP_ENV}")
        
        from app.database import AsyncSessionLocal
        print(f"✓ Database module loaded")
        
        # Test connection
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            result = await db.execute(text('SELECT 1 as test'))
            test_result = result.scalar()
            print(f"✓ Database connection successful: {test_result}")
            
            # Check ingestion jobs
            from app.models import IngestionJob
            result = await db.execute(text('SELECT COUNT(*) FROM ingestion_jobs'))
            count = result.scalar()
            print(f"✓ Total ingestion jobs: {count}")
            
            if count > 0:
                result = await db.execute(text('SELECT id, document_id, status, created_at FROM ingestion_jobs ORDER BY created_at DESC LIMIT 10'))
                jobs = result.fetchall()
                print(f"✓ Recent jobs:")
                for job in jobs:
                    print(f"  ID: {job[0]}, Doc: {job[1]}, Status: {job[2]}, Created: {job[3]}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())