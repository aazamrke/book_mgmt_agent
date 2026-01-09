from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from app.database import get_db
from app.models import IngestionJob, Document
from datetime import datetime, timedelta
import asyncio

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

@router.post("/trigger/{document_id}")
async def trigger_ingestion(document_id: int, db: AsyncSession = Depends(get_db)):
    # Check if document exists
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Create job
    job = IngestionJob(document_id=document_id, status="running")
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Simulate processing (in real app, this would be async background task)
    asyncio.create_task(process_ingestion_job(job.id))
    
    return {"message": "Ingestion started", "job_id": job.id}

async def process_ingestion_job(job_id: int):
    """Simulate ingestion processing"""
    await asyncio.sleep(2)  # Simulate processing time
    
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.status = "completed"
            await db.commit()

@router.get("/status/{job_id}")
async def ingestion_status(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job.status, "created_at": job.created_at}

@router.get("/jobs")
async def list_ingestion_jobs(db: AsyncSession = Depends(get_db)):
    """List all ingestion jobs with their status"""
    result = await db.execute(
        select(IngestionJob, Document.filename)
        .join(Document, IngestionJob.document_id == Document.id)
        .order_by(IngestionJob.created_at.desc())
    )
    jobs = result.all()
    
    return [
        {
            "id": job.IngestionJob.id,
            "document_id": job.IngestionJob.document_id,
            "filename": job.filename,
            "status": job.IngestionJob.status,
            "created_at": job.IngestionJob.created_at
        }
        for job in jobs
    ]

@router.get("/today-count")
async def today_processed_count(db: AsyncSession = Depends(get_db)):
    """Get today's processed job count"""
    today = datetime.now().date()
    
    result = await db.execute(
        select(func.count(IngestionJob.id))
        .where(
            and_(
                func.date(IngestionJob.created_at) == today,
                IngestionJob.status == "completed"
            )
        )
    )
    count = result.scalar() or 0
    
    return {"today_processed": count}

@router.post("/complete-stuck-jobs")
async def complete_stuck_jobs(db: AsyncSession = Depends(get_db)):
    """Complete jobs that are stuck in running status"""
    # Find jobs running for more than 5 minutes
    cutoff_time = datetime.now() - timedelta(minutes=5)
    
    result = await db.execute(
        select(IngestionJob)
        .where(
            and_(
                IngestionJob.status == "running",
                IngestionJob.created_at < cutoff_time
            )
        )
    )
    stuck_jobs = result.scalars().all()
    
    completed_count = 0
    for job in stuck_jobs:
        job.status = "completed"
        completed_count += 1
    
    await db.commit()
    
    return {
        "message": f"Completed {completed_count} stuck jobs",
        "completed_jobs": completed_count
    }
