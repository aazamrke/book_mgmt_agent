import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import app
from app.database import get_db
from app.models import User, Role, Book, Review
from app.security import hash_password, create_access_token

# Mock database session
class MockAsyncSession:
    def __init__(self):
        self.data = {}
        self.id_counter = 1
    
    async def execute(self, query):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        result.scalars.return_value.all.return_value = []
        return result
    
    def add(self, obj):
        obj.id = self.id_counter
        self.id_counter += 1
    
    async def commit(self):
        pass
    
    async def flush(self):
        pass
    
    async def refresh(self, obj):
        pass
    
    async def delete(self, obj):
        pass

@pytest.fixture
def mock_db():
    return MockAsyncSession()

@pytest.fixture
def client(mock_db):
    def override_get_db():
        yield mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin", "roles": ["admin"]})

@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def sample_book():
    book = Book(
        id=1,
        title="Test Book",
        author="Test Author", 
        genre="Fiction",
        year_published=2023,
        summary="A test book"
    )
    return book

@pytest.fixture
def admin_user():
    user = User(
        id=1,
        username="admin",
        password_hash=hash_password("password")
    )
    return user