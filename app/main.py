from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Book, Review
from app.crud import *
from app.llama3 import generate_summary, generate_summary_llama3
from app.auth import verify_user
from app.recommendations import recommend_books
from app.schemas import BookCreate, BookResponse, BookUpdate
from app.schemas import ReviewCreate, ReviewResponse
from app.models import Book
from typing import List
from app.routes import auth, users, documents, ingestion
from fastapi.middleware.cors import CORSMiddleware
from app.rag_pipeline_minimal import rag_pipeline

app = FastAPI(title="Intelligent Book Management System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(ingestion.router)

@app.post("/books",response_model=BookResponse)
async def add_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db)
):
    db_book = Book(**book.dict())
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    
    # Index book for RAG
    await rag_pipeline.index_book(db, db_book.id)
    
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
    
    # Reindex book for RAG
    await rag_pipeline.index_book(db, book.id)

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

@app.post(
    "/books/{book_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    # dependencies=[Depends(verify_user)]
)
async def add_review_for_book(
    book_id: int,
    review: ReviewCreate,
    db: AsyncSession = Depends(get_db)
):
    # Ensure book exists
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    db_review = Review(
        book_id=book_id,
        user_id=review.user_id,
        review_text=review.review_text,
        rating=review.rating,
    )

    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    
    # Reindex book to include new review
    await rag_pipeline.index_book(db, book_id)

    return db_review

@app.get(
    "/books/{book_id}/reviews",
    response_model=List[ReviewResponse]
)
async def get_reviews_for_book(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Ensure book exists
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    result = await db.execute(
        select(Review).where(Review.book_id == book_id)
    )
    reviews = result.scalars().all()

    return reviews


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


@app.post(
    "/books/{book_id}/generate-summary",
    response_model=dict,
    dependencies=[Depends(verify_user)]
)
async def generate_and_save_book_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    prompt = (
        f"Generate a concise summary for the book:\n"
        f"Title: {book.title}\n"
        f"Author: {book.author}\n"
        f"Genre: {book.genre}\n"
        f"Year Published: {book.year_published}\n"
    )

    summary = await generate_summary_llama3(prompt)

    book.summary = summary
    await db.commit()
    await db.refresh(book)

    return {
        "book_id": book.id,
        "summary": book.summary
    }

from app.schemas import GenerateSummaryRequest, GenerateSummaryResponse
from app.llama3 import generate_summary_llama3

@app.post(
    "/generate-summary",
    response_model=GenerateSummaryResponse,
)
async def generate_summary_from_content(
    payload: GenerateSummaryRequest
):
    summary = await generate_summary_llama3(
        f"Summarize the following book content:\n{payload.content}"
    )
    return GenerateSummaryResponse(summary=summary)


@app.get("/recommendations")
async def recommendations(genre: str, db: AsyncSession = Depends(get_db)):
    return await recommend_books(db, genre)

@app.post("/search")
async def search_books(query: str, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Search books using RAG pipeline with fallback"""
    # Try RAG search first
    results = rag_pipeline.search_similar_books(query, limit)
    
    # If no RAG results, do simple database search
    if not results:
        db_result = await db.execute(
            select(Book).where(
                Book.title.ilike(f"%{query}%") | 
                Book.author.ilike(f"%{query}%") |
                Book.genre.ilike(f"%{query}%")
            ).limit(limit)
        )
        books = db_result.scalars().all()
        
        results = [
            {
                "book_id": book.id,
                "similarity_score": 1.0,
                "metadata": {
                    "book_id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre
                },
                "content": f"Title: {book.title} Author: {book.author} Genre: {book.genre}"
            }
            for book in books
        ]
    
    return {"query": query, "results": results}

@app.get("/search")
async def search_books_get(query: str, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """GET version of search for UI compatibility"""
    return await search_books(query, limit, db)

@app.post("/books/{book_id}/reindex")
async def reindex_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """Manually reindex a book for RAG"""
    await rag_pipeline.index_book(db, book_id)
    return {"message": f"Book {book_id} reindexed successfully"}

@app.post("/reindex-all")
async def reindex_all_books(db: AsyncSession = Depends(get_db)):
    """Reindex all books for RAG"""
    result = await db.execute(select(Book))
    books = result.scalars().all()
    
    indexed_count = 0
    for book in books:
        try:
            await rag_pipeline.index_book(db, book.id)
            indexed_count += 1
        except Exception as e:
            print(f"Failed to index book {book.id}: {e}")
    
    return {
        "message": f"Reindexed {indexed_count} books successfully",
        "total_in_store": len(rag_pipeline.embeddings_store)
    }

@app.get("/debug/embeddings")
async def debug_embeddings():
    """Debug endpoint to check embeddings store"""
    return {
        "total_books_indexed": len(rag_pipeline.embeddings_store),
        "book_ids": list(rag_pipeline.embeddings_store.keys())
    }

