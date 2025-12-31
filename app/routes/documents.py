from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import Document
from app.auth import verify_user
from app.s3_service import s3_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to S3
        s3_key = await s3_service.upload_file(file_content, file.filename)
        
        if not s3_key:
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")
        
        # Save document record to database
        doc = Document(
            filename=file.filename,
            s3_key=s3_key,
            file_size=len(file_content)
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        return {
            "message": "Document uploaded successfully",
            "document_id": doc.id,
            "s3_key": s3_key,
            "download_url": s3_service.get_file_url(s3_key)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document))
    return result.scalars().all()

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_user)])
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.delete(document)
    await db.commit()
