from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Book, Review

class MinimalRAGPipeline:
    def __init__(self):
        self.embeddings_store = {}
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Simple hash-based embeddings for minimal footprint"""
        # Simple character frequency based embedding
        chars = {}
        for char in text.lower():
            chars[char] = chars.get(char, 0) + 1
        
        # Create 100-dim vector from character frequencies
        embedding = [0.0] * 100
        for i, char in enumerate(sorted(chars.keys())[:100]):
            embedding[i] = chars[char] / len(text)
        
        return embedding
    
    async def index_book(self, db: AsyncSession, book_id: int):
        """Index a book's content for search"""
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one_or_none()
            
            if not book:
                return
            
            reviews_result = await db.execute(select(Review).where(Review.book_id == book_id))
            reviews = reviews_result.scalars().all()
            
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
        except Exception:
            pass
    
    def search_similar_books(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Simple text matching search"""
        if not self.embeddings_store:
            return []
        
        query_lower = query.lower()
        results = []
        
        for book_id, data in self.embeddings_store.items():
            content_lower = data["content"].lower()
            
            # Simple keyword matching score
            score = 0.0
            for word in query_lower.split():
                if word in content_lower:
                    score += 1.0
            
            if score > 0:
                results.append({
                    "book_id": book_id,
                    "similarity_score": score / len(query_lower.split()),
                    "metadata": data["metadata"],
                    "content": data["content"]
                })
        
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:n_results]

# Global instance
rag_pipeline = MinimalRAGPipeline()