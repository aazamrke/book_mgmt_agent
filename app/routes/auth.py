from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import User, Role
from app.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])

class SignupRequest(BaseModel):
    username: str
    password: str

@router.post("/signup")
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Check if user exists
        result = await db.execute(select(User).where(User.username == data.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Get or create default user role
        user_role_result = await db.execute(select(Role).where(Role.name == "user"))
        user_role = user_role_result.scalar_one_or_none()
        
        if not user_role:
            user_role = Role(
                name="user",
                can_read=True,
                can_write=False,
                can_delete=False,
                is_admin=False
            )
            db.add(user_role)
            await db.flush()
        
        # Create user
        user = User(
            username=data.username,
            password_hash=hash_password(data.password)
        )
        db.add(user)
        await db.flush()
        
        # Assign default user role
        user.roles = [user_role]
        await db.commit()
        
        return {"message": "User registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Signup error: {str(e)}")

@router.post("/create-admin")
async def create_admin(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Check if admin role exists, create if not
        admin_role_result = await db.execute(select(Role).where(Role.name == "admin"))
        admin_role = admin_role_result.scalar_one_or_none()
        
        if not admin_role:
            admin_role = Role(
                name="admin",
                can_read=True,
                can_write=True,
                can_delete=True,
                is_admin=True
            )
            db.add(admin_role)
            await db.flush()
        
        # Create admin user
        user = User(
            username=data.username,
            password_hash=hash_password(data.password)
        )
        db.add(user)
        await db.flush()
        
        # Assign admin role
        user.roles = [admin_role]
        await db.commit()
        
        return {"message": "Admin user created successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/login")
async def login(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.username == data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Get user roles
        role_names = [role.name for role in user.roles] if user.roles else []

        token = create_access_token({
            "sub": user.username,
            "roles": role_names
        })

        return {
            "access_token": token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@router.post("/logout")
async def logout():
    return {"message": "Logout handled on client side (JWT invalidation)"}
