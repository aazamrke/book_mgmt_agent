from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, Boolean, DateTime, Table, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from app.database import Base

Base = declarative_base()
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    genre = Column(String)
    year_published = Column(Integer)
    summary = Column(Text)

    reviews = relationship("Review", back_populates="book")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    user_id = Column(Integer)
    review_text = Column(Text)
    rating = Column(Float)

    book = relationship("Book", back_populates="reviews")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="selectin"
    )


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    s3_key = Column(String(500))  # S3 object key
    file_size = Column(Integer)  # File size in bytes
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="uploaded")  # uploaded | ingested | failed

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    status = Column(String(50), default="pending")  # pending | running | completed | failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
