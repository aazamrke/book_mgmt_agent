from pydantic import BaseModel
from typing import Optional, List


class BookBase(BaseModel):
    title: str
    author: str
    genre: str
    year_published: int


class BookCreate(BookBase):
    pass


class BookResponse(BookBase):
    id: int
    summary: Optional[str] = None

    class Config:
        from_attributes = True  # ✅ REQUIRED for SQLAlchemy
