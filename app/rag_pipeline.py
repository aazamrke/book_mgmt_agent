import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Book, BookEmbedding, Review

class RAGPipeline:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings_store = {}  # In-memory store: {book_id: {"embedding": [...], "metadata": {...}, "content": "..."}}
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for given text"""
        return self.embedding_model.encode(text).tolist()
    
    async def index_book(self, db: AsyncSession, book_id: int):
        """Index a book's content for RAG retrieval"""
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        
        if not book:
            return
        
        # Get reviews for context
        reviews_result = await db.execute(select(Review).where(Review.book_id == book_id))
        reviews = reviews_result.scalars().all()
        
        # Create content for embedding
        content_parts = [
            f"Title: {book.title}",
            f"Author: {book.author}",
            f"Genre: {book.genre}",
        ]
        
        if book.summary:
            content_parts.append(f"Summary: {book.summary}")
        
        if reviews:
            review_texts = [r.review_text for r in reviews if r.review_text]
            if review_texts:
                content_parts.append(f"Reviews: {' '.join(review_texts[:3])}")
        
        content = " ".join(content_parts)
        embedding = self.generate_embeddings(content)
        
        # Store in memory
        self.embeddings_store[book_id] = {
            "embedding": embedding,
            "metadata": {
                "book_id": book_id,
                "title": book.title,
                "author": book.author,
                "genre": book.genre
            },
            "content": content
        }
        
        # Store in database
        # Check if embedding already exists
        existing_result = await db.execute(
            select(BookEmbedding).where(BookEmbedding.book_id == book_id)
        )
        existing_embedding = existing_result.scalar_one_or_none()
        
        if existing_embedding:
            existing_embedding.embedding_vector = json.dumps(embedding)
        else:
            db_embedding = BookEmbedding(
                book_id=book_id,
                content_type="full",
                embedding_vector=json.dumps(embedding)
            )
            db.add(db_embedding)
        
        await db.commit()
    
    def search_similar_books(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar books using RAG"""
        if not self.embeddings_store:
            return []
        
        query_embedding = np.array(self.generate_embeddings(query)).reshape(1, -1)
        
        results = []
        for book_id, data in self.embeddings_store.items():
            book_embedding = np.array(data["embedding"]).reshape(1, -1)
            similarity = cosine_similarity(query_embedding, book_embedding)[0][0]
            
            results.append({
                "book_id": book_id,
                "similarity_score": float(similarity),
                "metadata": data["metadata"],
                "content": data["content"]
            })
        
        # Sort by similarity score and return top results
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:n_results]

# Global instance
rag_pipeline = RAGPipeline()