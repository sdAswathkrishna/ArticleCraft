from fastapi import FastAPI, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Optional, List

# Import your modules
from generate_module import generator
# from nextword_module import generate_next_words, model as nextword_model, tokenizer, max_seq_len
from recommend_module import recommend_articles
from schemas import ArticleRequest, NextWordRequest, RecommendRequest, UserCreate, UserLogin, UserResponse, ArticleCreate, ArticleResponse, LikeResponse, GeneratedArticle
from models import User, Article, Like

from database import SessionLocal
from sqlalchemy.orm import Session
from database import get_db
import hashlib
import random

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# Initialize FastAPI
app = FastAPI(title="AI Article Platform", description="API for article generation, next word prediction, and article recommendation", version="1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")

# Load vector database at startup
@app.on_event("startup")
def startup_event():
    try:
        generator.load_vector_database()
    except Exception as e:
        raise RuntimeError(f"Error loading vector database: {str(e)}")


# Routes
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=UserResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    hashed_pwd = hash_password(user.password)
    db_user = db.query(User).filter(User.email == user.email, User.hashed_password == hashed_pwd).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return db_user

@app.post("/articles/create", response_model=ArticleResponse)
def create_article(
    article: ArticleCreate,
    user_id: int = Body(..., embed=True),  # later replace with session or token
    db: Session = Depends(get_db)
):
    new_article = Article(
        title=article.title,
        content=article.content,
        author_id=user_id
    )
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    return new_article

@app.get("/articles")
def get_random_articles(db: Session = Depends(get_db)):
    articles = db.query(
        Article.id,
        Article.title,
        Article.content,
        User.username.label("author_name")
    ).join(User, Article.author_id == User.id).all()

    article_list = [dict(row._mapping) for row in articles]
    return random.sample(article_list, min(len(article_list), 10))

@app.get("/articles/{article_id}")
def get_article_by_id(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    recommended_df = recommend_articles(article.title, top_k=5)
    recommendations = recommended_df.to_dict(orient="records")

    return {
        "article": {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "author_name": article.author.username
        },
        "recommended": recommendations
    }

@app.post("/articles/{article_id}/like", response_model=LikeResponse)
def like_article(article_id: int, user_id: int = Body(...), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    like = db.query(Like).filter(Like.user_id == user_id, Like.article_id == article_id).first()
    if like:
        db.delete(like)
        db.commit()
        raise HTTPException(status_code=200, detail="Unliked the article")

    new_like = Like(user_id=user_id, article_id=article_id)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return new_like


@app.get("/users/{user_id}/articles", response_model=List[ArticleResponse])
def get_user_articles(user_id: int, db: Session = Depends(get_db)):
    articles = db.query(Article).filter(Article.author_id == user_id).order_by(Article.created_at.desc()).all()
    return articles


@app.post("/articles/generate", response_model=GeneratedArticle)
def generate_article_content(
    request: ArticleRequest,
    user_id: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    try:
        result = generator.generate_article(request.title, request.num_similar_articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    return {
    "title": request.title,
    "content": result["article"],
    "author_id": user_id
}


# @app.post("/predict-nextwords/")
# def predict_next_words(request: NextWordRequest):
#     try:
#         result = generate_next_words(request.seed_text, nextword_model, tokenizer, max_seq_len, request.num_words)
#         return {"input": request.seed_text, "output": result}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend-articles/")
def recommend(request: RecommendRequest):
    try:
        results_df = recommend_articles(request.query, request.top_k)
        results = results_df.to_dict(orient="records")
        return {"query": request.query, "recommendations": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))