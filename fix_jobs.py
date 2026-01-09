#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def fix_stuck_jobs():
    try:
        from app.database import AsyncSessionLocal
        from app.models import IngestionJob
        from sqlalchemy import select, and_
        from datetime import datetime, timedelta
        
        async with AsyncSessionLocal() as db:
            # Get all running jobs
            result = await db.execute(
                select(IngestionJob).where(IngestionJob.status == "running")
            )
            stuck_jobs = result.scalars().all()
            
            print(f"Found {len(stuck_jobs)} stuck jobs")
            
            # Complete them all
            completed_count = 0
            for job in stuck_jobs:
                job.status = "completed"
                completed_count += 1
                print(f"Completing job {job.id} (document {job.document_id})")
            
            await db.commit()
            print(f"[OK] Completed {completed_count} stuck jobs")
            
            # Show current stats
            total_result = await db.execute(select(IngestionJob))
            all_jobs = total_result.scalars().all()
            
            status_counts = {}
            for job in all_jobs:
                status_counts[job.status] = status_counts.get(job.status, 0) + 1
            
            print(f"Current job status counts: {status_counts}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_stuck_jobs())