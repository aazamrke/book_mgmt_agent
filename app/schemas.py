from pydantic import BaseModel
from typing import Optional, List


class BookBase(BaseModel):
    title: str
    author_id: int
    genre_id: int
    year_published: int

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[int] = None
    genre_id: Optional[int] = None
    year_published: Optional[int] = None
    summary: Optional[str] = None

class BookResponse(BaseModel):
    id: int
    title: str
    author_id: int
    genre_id: int
    year_published: int
    summary: Optional[str] = None
    author_name: Optional[str] = None
    genre_name: Optional[str] = None

    class Config:
        from_attributes = True

class AuthorCreate(BaseModel):
    name: str

class AuthorResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class GenreCreate(BaseModel):
    name: str

class GenreResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class AuthorUpdate(BaseModel):
    name: Optional[str] = None

class GenreUpdate(BaseModel):
    name: Optional[str] = None

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