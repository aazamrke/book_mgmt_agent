from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import Document
from app.auth import verify_user
from app.s3_service import s3_service
from app.config import settings
import io

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Read file content for S3 upload if needed
        file_content = await file.read()
        
        # Upload based on environment (S3 in production, local in development)
        file_path = await s3_service.upload_file(file_content, file.filename)
        
        if not file_path:
            raise HTTPException(status_code=500, detail="Failed to upload file")
        
        # Save document record with file size
        doc = Document(
            filename=file.filename,
            file_size=len(file_content)
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        response = {
            "message": "Document uploaded successfully",
            "document_id": doc.id,
            "filename": file.filename,
            "file_size": len(file_content)
        }
        
        # Add S3 info only in production
        if settings.USE_S3:
            response["s3_key"] = file_path
            response["download_url"] = s3_service.get_file_url(file_path)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document))
    documents = result.scalars().all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "status": doc.status,
            "file_size": doc.file_size or 0,
            "uploaded_by": doc.uploaded_by,
            "download_url": f"/documents/{doc.id}/download"
        }
        for doc in documents
    ]

@router.get("/{document_id}/download")
async def download_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # In development, return a placeholder file
    if not settings.USE_S3:
        # Create a simple text file with document info
        content = f"Document: {document.filename}\nUploaded: {document.uploaded_at}\nSize: {document.file_size} bytes"
        file_like = io.BytesIO(content.encode())
        
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={document.filename}"}
        )
    
    # In production, redirect to S3 presigned URL
    try:
        download_url = s3_service.get_file_url(document.filename)  # Using filename as S3 key for now
        if download_url:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=download_url)
        else:
            raise HTTPException(status_code=404, detail="File not found in storage")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_user)])
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.delete(document)
    await db.commit()