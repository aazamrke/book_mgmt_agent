#!/usr/bin/env python3
"""
Script to update the roles table with permission columns
"""
import asyncio
import asyncpg
from app.config import settings

async def update_roles_table():
    """Add permission columns to roles table if they don't exist"""
    
    # Parse database URL to get connection parameters
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Check if columns exist and add them if they don't
        columns_to_add = [
            ("can_read", "BOOLEAN DEFAULT TRUE"),
            ("can_write", "BOOLEAN DEFAULT FALSE"), 
            ("can_delete", "BOOLEAN DEFAULT FALSE"),
            ("is_admin", "BOOLEAN DEFAULT FALSE")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                # Try to add the column
                await conn.execute(f"ALTER TABLE roles ADD COLUMN {column_name} {column_def}")
                print(f"Added column: {column_name}")
            except asyncpg.DuplicateColumnError:
                print(f"Column {column_name} already exists")
            except Exception as e:
                print(f"Error adding column {column_name}: {e}")
        
        # Update existing roles to have default permissions
        await conn.execute("""
            UPDATE roles 
            SET can_read = TRUE, can_write = FALSE, can_delete = FALSE, is_admin = FALSE 
            WHERE can_read IS NULL
        """)
        
        print("Roles table updated successfully!")
        
    except Exception as e:
        print(f"Error updating roles table: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(update_roles_table())