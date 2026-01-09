import asyncio
import asyncpg
from app.config import settings

async def assign_default_roles():
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Create default 'user' role if it doesn't exist
        await conn.execute("""
            INSERT INTO roles (name, can_read, can_write, can_delete, is_admin)
            VALUES ('user', TRUE, FALSE, FALSE, FALSE)
            ON CONFLICT (name) DO NOTHING
        """)
        
        # Get the user role ID
        user_role = await conn.fetchrow("SELECT id FROM roles WHERE name = 'user'")
        user_role_id = user_role['id']
        
        # Find users without any roles
        users_without_roles = await conn.fetch("""
            SELECT u.id, u.username 
            FROM users u 
            LEFT JOIN user_roles ur ON u.id = ur.user_id 
            WHERE ur.user_id IS NULL
        """)
        
        # Assign default role to users without roles
        for user in users_without_roles:
            await conn.execute("""
                INSERT INTO user_roles (user_id, role_id) 
                VALUES ($1, $2)
            """, user['id'], user_role_id)
            print(f"Assigned 'user' role to: {user['username']}")
        
        print(f"Assigned default roles to {len(users_without_roles)} users")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(assign_default_roles())