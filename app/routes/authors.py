from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Author
from app.schemas import AuthorCreate, AuthorResponse
from typing import List

router = APIRouter(prefix="/authors", tags=["Authors"])

@router.post("/", response_model=AuthorResponse)
async def create_author(author: AuthorCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Author).where(Author.name == author.name))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Author already exists")
        
        db_author = Author(name=author.name)
        db.add(db_author)
        await db.commit()
        await db.refresh(db_author)
        return db_author
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create author")

@router.get("/", response_model=List[AuthorResponse])
async def get_authors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Author).order_by(Author.name))
    return result.scalars().all()