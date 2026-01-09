import asyncio
from app.database import AsyncSessionLocal
from app.models import IngestionJob
from sqlalchemy import select, func, and_
from datetime import datetime

async def get_stats():
    async with AsyncSessionLocal() as db:
        # Get all jobs
        result = await db.execute(select(IngestionJob))
        all_jobs = result.scalars().all()
        
        print(f"Total jobs: {len(all_jobs)}")
        
        today = datetime.now().date()
        print(f"Today's date: {today}")
        
        # Check each job
        today_completed = 0
        for job in all_jobs:
            job_date = job.created_at.date() if job.created_at else None
            is_today = job_date == today if job_date else False
            is_completed = job.status == "completed"
            
            print(f"Job {job.id}: {job.created_at} -> {job_date} -> Today: {is_today}, Status: {job.status}")
            
            if is_today and is_completed:
                today_completed += 1
        
        print(f"Today completed count: {today_completed}")

asyncio.run(get_stats())