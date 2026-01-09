from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import User, Role, user_roles
from app.auth import verify_admin
from app.security import hash_password
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role_names: List[str] = []

class UpdateUserRequest(BaseModel):
    username: str = None
    is_active: bool = None
    role_names: List[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    roles: List[str]

@router.post("/", response_model=dict)
async def create_user(user_data: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Check if user exists
        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create user
        user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Assign roles after user is committed
        if user_data.role_names:
            role_result = await db.execute(select(Role).where(Role.name.in_(user_data.role_names)))
            roles = role_result.scalars().all()
            if len(roles) != len(user_data.role_names):
                found_roles = [r.name for r in roles]
                missing_roles = [r for r in user_data.role_names if r not in found_roles]
                raise HTTPException(status_code=400, detail=f"Roles not found: {missing_roles}")
            user.roles = roles
            await db.commit()
        return {"message": "User created successfully", "user_id": user.id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(verify_admin)])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).options(selectinload(User.roles)))
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            is_active=user.is_active,
            roles=[role.name for role in user.roles]
        )
        for user in users
    ]

@router.put("/{user_id}", response_model=dict, dependencies=[Depends(verify_admin)])
async def update_user(user_id: int, user_data: UpdateUserRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    if user_data.username:
        user.username = user_data.username
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    # Update roles
    if user_data.role_names is not None:
        role_result = await db.execute(select(Role).where(Role.name.in_(user_data.role_names)))
        roles = role_result.scalars().all()
        user.roles = roles
    
    await db.commit()
    return {"message": "User updated successfully"}

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_admin)])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()

@router.get("/roles", response_model=List[dict], dependencies=[Depends(verify_admin)])
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role))
    roles = result.scalars().all()
    return [{
        "id": role.id, 
        "name": role.name,
        "can_read": role.can_read,
        "can_write": role.can_write,
        "can_delete": role.can_delete,
        "is_admin": role.is_admin
    } for role in roles]

class CreateRoleRequest(BaseModel):
    name: str
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False
    is_admin: bool = False

@router.post("/roles", response_model=dict, dependencies=[Depends(verify_admin)])
async def create_role(role_data: CreateRoleRequest, db: AsyncSession = Depends(get_db)):
    # Check if role exists
    result = await db.execute(select(Role).where(Role.name == role_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role already exists")
    
    role = Role(
        name=role_data.name,
        can_read=role_data.can_read,
        can_write=role_data.can_write,
        can_delete=role_data.can_delete,
        is_admin=role_data.is_admin
    )
    db.add(role)
    await db.commit()
    return {"message": "Role created successfully", "role_id": role.id}

@router.post("/{user_id}/assign-role")
async def assign_role_to_user(user_id: int, role_name: str, db: AsyncSession = Depends(get_db)):
    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get role
    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Assign role
    if role not in user.roles:
        user.roles.append(role)
        await db.commit()
    
    return {"message": f"Role '{role_name}' assigned to user '{user.username}'"}

@router.delete("/{user_id}/remove-role")
async def remove_role_from_user(user_id: int, role_name: str, db: AsyncSession = Depends(get_db)):
    # Get user with roles
    user_result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find and remove role
    role_to_remove = None
    for role in user.roles:
        if role.name == role_name:
            role_to_remove = role
            break
    
    if not role_to_remove:
        raise HTTPException(status_code=404, detail="User does not have this role")
    
    user.roles.remove(role_to_remove)
    await db.commit()
    
    return {"message": f"Role '{role_name}' removed from user '{user.username}'"}

@router.get("/{user_id}/roles")
async def get_user_roles(user_id: int, db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user.id,
        "username": user.username,
        "roles": [role.name for role in user.roles]
    }