import asyncio
import asyncpg
from app.config import settings

async def add_file_size_column():
    conn = await asyncpg.connect(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    try:
        # Add file_size column if it doesn't exist
        await conn.execute("""
            ALTER TABLE documents 
            ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0
        """)
        print("Added file_size column to documents table")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_file_size_column())