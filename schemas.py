from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


# User
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True


# Article
class ArticleBase(BaseModel):
    title: str
    content: str

class ArticleCreate(ArticleBase):
    pass

class ArticleResponse(ArticleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    author_id: int

    class Config:
        orm_mode = True


# Like
class LikeResponse(BaseModel):
    user_id: int
    article_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class GeneratedArticle(BaseModel):
    title: str
    content: str
    author_id: int


# ML module request schemas

class ArticleRequest(BaseModel):
    title: str
    num_similar_articles: Optional[int] = 3

class NextWordRequest(BaseModel):
    seed_text: str
    num_words: Optional[int] = 10

class RecommendRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
