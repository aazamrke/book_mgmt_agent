from sqlalchemy.future import select
from app.models import Book, Review

async def create_book(db, book):
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book

async def get_books(db):
    result = await db.execute(select(Book))
    return result.scalars().all()

async def add_review(db, review):
    db.add(review)
    await db.commit()
    return review
