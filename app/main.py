from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Book, Review
from app.crud import *
from app.llama3 import generate_summary
from app.auth import verify_user
from app.recommendations import recommend_books
from app.schemas import BookCreate, BookResponse
from app.models import Book
from typing import List

app = FastAPI(title="Intelligent Book Management System")

@app.post("/books",response_model=BookResponse)
async def add_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db)
):
    db_book = Book(**book.dict())
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book

@app.get("/books", response_model=List[BookResponse])
async def get_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book))
    return result.scalars().all()

# @app.post("/books/{id}/reviews")
# async def add_book_review(id: int, review: Review, db: AsyncSession = Depends(get_db)):
#     review.book_id = id
#     return await add_review(db, review)

@app.get("/books/{id}/summary")
async def book_summary(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.book_id == id))
    reviews = result.scalars().all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews)
    summary = await generate_summary(" ".join(r.review_text for r in reviews))
    return {"rating": avg_rating, "review_summary": summary}

@app.get("/recommendations")
async def recommendations(genre: str, db: AsyncSession = Depends(get_db)):
    return await recommend_books(db, genre)
