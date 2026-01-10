from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Application imports
from app.config import settings
from app.logging_config import setup_logging, get_logger
from app.middleware import RequestTrackingMiddleware, error_handler, get_metrics_data, MetricsMiddleware
from app.database import get_db, init_database, close_database, db_health
from app.models import Book, Review, Author, Genre
from app.crud import *
from app.llama3_minimal import generate_summary, generate_summary_llama3
from app.auth import verify_user
from app.recommendations import recommend_books
from app.schemas import BookCreate, BookResponse, BookUpdate, ReviewCreate, ReviewResponse, AuthorCreate, AuthorResponse, GenreCreate, GenreResponse, AuthorUpdate, GenreUpdate
from app.schemas import GenerateSummaryRequest, GenerateSummaryResponse
from app.rag_pipeline_minimal import rag_pipeline
from app.routes import auth, users, documents, ingestion

from typing import List
import time
import asyncio

# Setup logging
setup_logging(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # Warm up services
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    try:
        await close_database()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

# Create FastAPI application with production configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade intelligent book management system with RAG capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Security middleware
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual domains in production
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(MetricsMiddleware)

# Global exception handler
app.add_exception_handler(Exception, error_handler)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(ingestion.router)

# Author and Genre Management
@app.post("/authors", response_model=AuthorResponse, tags=["Authors"])
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

@app.get("/authors", response_model=List[AuthorResponse], tags=["Authors"])
async def get_authors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Author).order_by(Author.name))
    return result.scalars().all()

@app.put("/authors/{author_id}", response_model=AuthorResponse, tags=["Authors"])
async def update_author(author_id: int, author_update: AuthorUpdate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Author).where(Author.id == author_id))
        author = result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")
        
        if author_update.name is not None:
            # Check if name already exists
            existing = await db.execute(select(Author).where(Author.name == author_update.name, Author.id != author_id))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Author name already exists")
            author.name = author_update.name
        
        await db.commit()
        await db.refresh(author)
        return author
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update author")

@app.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Authors"])
async def delete_author(author_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Author).where(Author.id == author_id))
        author = result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")
        
        # Check if author has books
        books_result = await db.execute(select(Book).where(Book.author_id == author_id))
        if books_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Cannot delete author with existing books")
        
        await db.delete(author)
        await db.commit()
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete author")

@app.post("/genres", response_model=GenreResponse, tags=["Genres"])
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

@app.get("/genres", response_model=List[GenreResponse], tags=["Genres"])
async def get_genres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Genre).order_by(Genre.name))
    return result.scalars().all()

@app.put("/genres/{genre_id}", response_model=GenreResponse, tags=["Genres"])
async def update_genre(genre_id: int, genre_update: GenreUpdate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Genre).where(Genre.id == genre_id))
        genre = result.scalar_one_or_none()
        if not genre:
            raise HTTPException(status_code=404, detail="Genre not found")
        
        if genre_update.name is not None:
            # Check if name already exists
            existing = await db.execute(select(Genre).where(Genre.name == genre_update.name, Genre.id != genre_id))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Genre name already exists")
            genre.name = genre_update.name
        
        await db.commit()
        await db.refresh(genre)
        return genre
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update genre")

@app.delete("/genres/{genre_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Genres"])
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Genre).where(Genre.id == genre_id))
        genre = result.scalar_one_or_none()
        if not genre:
            raise HTTPException(status_code=404, detail="Genre not found")
        
        # Check if genre has books
        books_result = await db.execute(select(Book).where(Book.genre_id == genre_id))
        if books_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Cannot delete genre with existing books")
        
        await db.delete(genre)
        await db.commit()
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete genre")

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with database and metrics"""
    db_healthy = await db_health.check_health()
    app_metrics = get_metrics_data()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "database": {
            "status": "healthy" if db_healthy else "unhealthy",
            "last_check": db_health.last_check
        },
        "metrics": app_metrics
    }

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Application metrics endpoint"""
    return get_metrics_data()


@app.post("/books", response_model=BookResponse, tags=["Books"])
async def add_book(book: BookCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Verify author and genre exist
        author_result = await db.execute(select(Author).where(Author.id == book.author_id))
        if not author_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Author not found")
        
        genre_result = await db.execute(select(Genre).where(Genre.id == book.genre_id))
        if not genre_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Genre not found")
        
        db_book = Book(**book.dict())
        db.add(db_book)
        await db.commit()
        await db.refresh(db_book)
        
        # Index book for RAG
        asyncio.create_task(rag_pipeline.index_book(db, db_book.id))
        
        logger.info(f"Book created: {db_book.id}", extra={"book_id": db_book.id})
        return db_book
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create book: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create book")

@app.get("/books", response_model=List[BookResponse], tags=["Books"])
async def get_books(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Book, Author.name.label("author_name"), Genre.name.label("genre_name"))
            .join(Author, Book.author_id == Author.id)
            .join(Genre, Book.genre_id == Genre.id)
        )
        books_data = result.all()
        
        books = []
        for book, author_name, genre_name in books_data:
            book_dict = {
                "id": book.id,
                "title": book.title,
                "author_id": book.author_id,
                "genre_id": book.genre_id,
                "year_published": book.year_published,
                "summary": book.summary,
                "author_name": author_name,
                "genre_name": genre_name
            }
            books.append(BookResponse(**book_dict))
        
        logger.info(f"Retrieved {len(books)} books")
        return books
    except Exception as e:
        logger.error(f"Failed to retrieve books: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve books")

@app.get("/books/{book_id}", response_model=BookResponse, tags=["Books"])
async def get_book_by_id(book_id: int, db: AsyncSession = Depends(get_db)):
    """Get book by ID with proper error handling"""
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )
        
        logger.info(f"Retrieved book: {book_id}", extra={"book_id": book_id})
        return book
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve book {book_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve book")

@app.put("/books/{book_id}", response_model=BookResponse, tags=["Books"])
async def update_book(book_id: int, book_update: BookUpdate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Verify author and genre if provided
        if book_update.author_id is not None:
            author_result = await db.execute(select(Author).where(Author.id == book_update.author_id))
            if not author_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Author not found")
            book.author_id = book_update.author_id
        
        if book_update.genre_id is not None:
            genre_result = await db.execute(select(Genre).where(Genre.id == book_update.genre_id))
            if not genre_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Genre not found")
            book.genre_id = book_update.genre_id
        
        if book_update.title is not None:
            book.title = book_update.title
        if book_update.year_published is not None:
            book.year_published = book_update.year_published
        if book_update.summary is not None:
            book.summary = book_update.summary
        
        await db.commit()
        await db.refresh(book)
        return book
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update book")

@app.get("/books/dropdown/authors", response_model=List[AuthorResponse], tags=["Books"])
async def get_authors_dropdown(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Author).order_by(Author.name))
    return result.scalars().all()

@app.get("/books/dropdown/genres", response_model=List[GenreResponse], tags=["Books"])
async def get_genres_dropdown(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Genre).order_by(Genre.name))
    return result.scalars().all()

# Search and RAG endpoints
@app.post("/search", tags=["Search"])
@app.get("/search", tags=["Search"])
async def search_books(query: str, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Semantic book search with fallback"""
    try:
        # Try RAG search first
        results = rag_pipeline.search_similar_books(query, limit)
        
        # Fallback to database search if no RAG results
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
        
        logger.info(f"Search completed: '{query}' returned {len(results)} results")
        return {"query": query, "results": results}
        
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")

# Additional endpoints with proper error handling
@app.post("/reindex-all", tags=["Search"])
async def reindex_all_books(db: AsyncSession = Depends(get_db)):
    """Reindex all books for RAG with progress tracking"""
    try:
        result = await db.execute(select(Book))
        books = result.scalars().all()
        
        indexed_count = 0
        for book in books:
            try:
                await rag_pipeline.index_book(db, book.id)
                indexed_count += 1
            except Exception as e:
                logger.warning(f"Failed to index book {book.id}: {str(e)}")
        
        logger.info(f"Reindexed {indexed_count}/{len(books)} books")
        return {
            "message": f"Reindexed {indexed_count} books successfully",
            "total_books": len(books),
            "indexed_count": indexed_count,
            "total_in_store": len(rag_pipeline.embeddings_store)
        }
        
    except Exception as e:
        logger.error(f"Reindexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Reindexing failed")

@app.get("/debug/embeddings", tags=["Debug"])
async def debug_embeddings():
    """Debug endpoint for embeddings store"""
    if not settings.is_development:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "total_books_indexed": len(rag_pipeline.embeddings_store),
        "book_ids": list(rag_pipeline.embeddings_store.keys())
    }

@app.get("/dashboard/stats", tags=["Dashboard"])
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics including today's processed count"""
    from datetime import datetime
    from sqlalchemy import func, and_
    from app.models import IngestionJob
    
    today = datetime.now().date()
    
    result = await db.execute(
        select(func.count(IngestionJob.id))
        .where(
            and_(
                func.date(IngestionJob.created_at) == today,
                IngestionJob.status == "completed"
            )
        )
    )
    today_processed = result.scalar() or 0
    
    return {"today_processed": today_processed}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS if settings.is_production else 1,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        reload=settings.is_development
    )