import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.models import Author, Genre, Book

async def migrate_to_foreign_keys():
    async for db in get_db():
        try:
            # Create authors and genres tables
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS authors (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR UNIQUE NOT NULL
                );
            """))
            
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS genres (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR UNIQUE NOT NULL
                );
            """))
            
            # Migrate existing data
            # Get unique authors
            result = await db.execute(text("SELECT DISTINCT author FROM books WHERE author IS NOT NULL"))
            authors = result.fetchall()
            
            for (author_name,) in authors:
                if author_name and author_name.strip():
                    await db.execute(
                        text("INSERT INTO authors (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
                        {"name": author_name.strip()}
                    )
            
            # Get unique genres
            result = await db.execute(text("SELECT DISTINCT genre FROM books WHERE genre IS NOT NULL"))
            genres = result.fetchall()
            
            for (genre_name,) in genres:
                if genre_name and genre_name.strip():
                    await db.execute(
                        text("INSERT INTO genres (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
                        {"name": genre_name.strip()}
                    )
            
            # Add new columns to books table
            await db.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS author_id INTEGER"))
            await db.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS genre_id INTEGER"))
            
            # Update books with foreign keys
            await db.execute(text("""
                UPDATE books SET author_id = authors.id 
                FROM authors 
                WHERE books.author = authors.name AND books.author_id IS NULL
            """))
            
            await db.execute(text("""
                UPDATE books SET genre_id = genres.id 
                FROM genres 
                WHERE books.genre = genres.name AND books.genre_id IS NULL
            """))
            
            # Add foreign key constraints (PostgreSQL doesn't support IF NOT EXISTS for constraints)
            try:
                await db.execute(text("""
                    ALTER TABLE books 
                    ADD CONSTRAINT fk_books_author 
                    FOREIGN KEY (author_id) REFERENCES authors(id)
                """))
            except:
                pass  # Constraint might already exist
            
            try:
                await db.execute(text("""
                    ALTER TABLE books 
                    ADD CONSTRAINT fk_books_genre 
                    FOREIGN KEY (genre_id) REFERENCES genres(id)
                """))
            except:
                pass  # Constraint might already exist
            
            # Make columns NOT NULL after data migration
            await db.execute(text("ALTER TABLE books ALTER COLUMN author_id SET NOT NULL"))
            await db.execute(text("ALTER TABLE books ALTER COLUMN genre_id SET NOT NULL"))
            
            await db.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"Migration failed: {e}")
        break

if __name__ == "__main__":
    asyncio.run(migrate_to_foreign_keys())