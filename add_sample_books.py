import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Book

async def add_sample_books():
    async for db in get_db():
        # Sample books with authors and genres
        books = [
            Book(title="The Great Gatsby", author="F. Scott Fitzgerald", genre="Fiction", year_published=1925),
            Book(title="To Kill a Mockingbird", author="Harper Lee", genre="Fiction", year_published=1960),
            Book(title="1984", author="George Orwell", genre="Dystopian", year_published=1949),
            Book(title="Pride and Prejudice", author="Jane Austen", genre="Romance", year_published=1813),
            Book(title="The Catcher in the Rye", author="J.D. Salinger", genre="Fiction", year_published=1951),
            Book(title="Dune", author="Frank Herbert", genre="Science Fiction", year_published=1965),
            Book(title="The Hobbit", author="J.R.R. Tolkien", genre="Fantasy", year_published=1937),
            Book(title="Brave New World", author="Aldous Huxley", genre="Dystopian", year_published=1932),
        ]
        
        for book in books:
            db.add(book)
        
        await db.commit()
        print(f"Added {len(books)} sample books")
        break

if __name__ == "__main__":
    asyncio.run(add_sample_books())