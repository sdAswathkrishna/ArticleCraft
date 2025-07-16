from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== ARTICLE SCHEMAS ====================

class ArticleBase(BaseModel):
    title: str
    content: str
    tags: Optional[str] = None

class ArticleCreate(ArticleBase):
    generated: bool = False

class ArticleResponse(ArticleBase):
    id: int
    generated: bool
    timestamp: datetime
    author_id: int
    author: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

class ArticleWithStats(ArticleResponse):
    views_count: int = 0
    likes_count: int = 0

# ==================== AUTH SCHEMAS ====================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ==================== AI FEATURE SCHEMAS ====================

class GenerateRequest(BaseModel):
    title: str

class GenerateResponse(BaseModel):
    content: str

class ArticleGenerateRequest(BaseModel):
    title: str
    num_similar_articles: int = 3

class PredictRequest(BaseModel):
    seed_text: str

class PredictResponse(BaseModel):
    predictions: List[str]

class NextWordRequest(BaseModel):
    seed_text: str
    next_words: int = 5
    temperature: float = 1.0

class RecommendationRequest(BaseModel):
    query: str
    top_k: int = 5

# ==================== ENGAGEMENT SCHEMAS ====================

class ViewResponse(BaseModel):
    id: int
    user_id: Optional[int]
    article_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class LikeResponse(BaseModel):
    id: int
    user_id: int
    article_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

# ==================== RECOMMENDATION SCHEMAS ====================

class RecommendationResponse(BaseModel):
    id: int
    title: str
    content: str