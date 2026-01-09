from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Genre
from app.schemas import GenreCreate, GenreResponse
from typing import List

router = APIRouter(prefix="/genres", tags=["Genres"])

@router.post("/", response_model=GenreResponse)
async def create_genre(genre: GenreCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Genre).where(Genre.name == genre.name))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Genre already exists")
        
        db_genre = Genre(name=genre.name)
        db.add(db_genre)
        await db.commit()
        await db.refresh(db_genre)
        return db_genre
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create genre")

@router.get("/", response_model=List[GenreResponse])
async def get_genres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Genre).order_by(Genre.name))
    return result.scalars().all()