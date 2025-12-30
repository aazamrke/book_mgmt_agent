from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Book, Review
from app.crud import *
from app.llama3 import generate_summary
from app.auth import verify_user
from app.recommendations import recommend_books
from app.schemas import BookCreate, BookResponse, BookUpdate
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

@app.get("/books/{book_id}",response_model=BookResponse)
async def get_book_by_id(book_id: int,db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book

@app.put("/books/{book_id}",response_model=BookResponse,dependencies=[Depends(verify_user)])
async def update_book_by_id(book_id: int,book_update: BookUpdate,db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    update_data = book_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(book, key, value)

    await db.commit()
    await db.refresh(book)

    return book

@app.delete("/books/{book_id}",status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(verify_user)])
async def delete_book_by_id(book_id: int,db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    await db.delete(book)
    await db.commit()



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
