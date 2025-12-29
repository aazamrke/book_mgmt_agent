from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Book
from sqlalchemy.future import select

async def recommend_books(db, genre: str):
    result = await db.execute(
        select(Book).where(Book.genre == genre)
    )
    return result.scalars().all()
