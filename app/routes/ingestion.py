from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import IngestionJob

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

@router.post("/trigger/{document_id}")
async def trigger_ingestion(document_id: int, db: AsyncSession = Depends(get_db)):
    job = IngestionJob(document_id=document_id, status="running")
    db.add(job)
    await db.commit()
    return {"message": "Ingestion started", "job_id": job.id}

@router.get("/status/{job_id}")
async def ingestion_status(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    job = result.scalar_one_or_none()
    return {"status": job.status}
