from pydantic import BaseModel
from typing import Optional, List


class BookBase(BaseModel):
    title: str
    author: str
    genre: str
    year_published: int


class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    year_published: Optional[int] = None
    summary: Optional[str] = None

class BookResponse(BookBase):
    id: int
    summary: Optional[str] = None

    class Config:
        from_attributes = True  # ✅ REQUIRED for SQLAlchemy

class ReviewCreate(BaseModel):
    user_id: int
    review_text: str
    rating: float


class ReviewResponse(ReviewCreate):
    id: int
    book_id: int

    class Config:
        from_attributes = True

class GenerateSummaryRequest(BaseModel):
    content: str

class GenerateSummaryResponse(BaseModel):
    summary: str