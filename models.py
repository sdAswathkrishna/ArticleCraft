from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database configuration
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./articlecraft.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User Model
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    articles = relationship("Article", back_populates="author")
    views = relationship("View", back_populates="viewer")
    likes = relationship("Like", back_populates="liker")

# Article Model
class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tags = Column(Text)
    generated = Column(Boolean, default=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationships
    author = relationship("User", back_populates="articles")
    views = relationship("View", back_populates="article")
    likes = relationship("Like", back_populates="article")

# View Model
class View(Base):
    __tablename__ = 'views'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Allow anonymous views
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    viewer = relationship("User", back_populates="views")
    article = relationship("Article", back_populates="views")

# Like Model
class Like(Base):
    __tablename__ = 'likes'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    liker = relationship("User", back_populates="likes")
    article = relationship("Article", back_populates="likes")