from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

# Import custom modules
from models import User, Article, View, Like, get_db, Base, engine
from schemas import (
    UserCreate, UserLogin, UserResponse, ArticleCreate, ArticleResponse,
    ArticleWithStats, Token, GenerateRequest, PredictRequest, NextWordRequest,
    RecommendationRequest, ArticleGenerateRequest, ViewResponse, LikeResponse
)
from auth import (
    authenticate_user, create_access_token, get_current_user,
    get_password_hash, get_current_user_optional, ACCESS_TOKEN_EXPIRE_MINUTES
)
from services import ai_services

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    Base.metadata.create_all(bind=engine)
    await ai_services.load_all_models()
    yield
    # Shutdown
    print("Shutting down...")

# FastAPI App
app = FastAPI(
    title="ArticleCraft API",
    description="Article generation and recommendation API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==================== HTML ROUTES ====================

@app.get("/")
async def home():
    return FileResponse("templates/home.html")

@app.get("/login")
async def login_page():
    return FileResponse("templates/login.html")

@app.get("/register")
async def register_page():
    return FileResponse("templates/register.html")

@app.get("/write")
async def write_page():
    return FileResponse("templates/write.html")

@app.get("/generate")
async def generate_page():
    return FileResponse("templates/generate.html")

@app.get("/profile")
async def profile_page():
    return FileResponse("templates/profile.html")

@app.get("/article/{article_id}")
async def article_page(article_id: int):
    return FileResponse("templates/article.html")

# ==================== AUTH ROUTES ====================

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/auth/login", response_model=Token)
async def login_for_access_token(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ==================== USER ROUTES ====================

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/users/me/articles", response_model=List[ArticleWithStats])
async def get_user_articles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    articles = db.query(Article).filter(Article.author_id == current_user.id).order_by(Article.timestamp.desc()).all()
    
    articles_with_stats = []
    for article in articles:
        views_count = db.query(View).filter(View.article_id == article.id).count()
        likes_count = db.query(Like).filter(Like.article_id == article.id).count()
        
        article_data = ArticleWithStats(
            id=article.id,
            title=article.title,
            content=article.content,
            tags=article.tags,
            generated=article.generated,
            timestamp=article.timestamp,
            author_id=article.author_id,
            views_count=views_count,
            likes_count=likes_count
        )
        articles_with_stats.append(article_data)
    
    return articles_with_stats

# ==================== ARTICLE ROUTES ====================

@app.get("/articles/", response_model=List[ArticleWithStats])
async def get_articles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    articles = db.query(Article).order_by(Article.timestamp.desc()).offset(skip).limit(limit).all()
    
    articles_with_stats = []
    for article in articles:
        views_count = db.query(View).filter(View.article_id == article.id).count()
        likes_count = db.query(Like).filter(Like.article_id == article.id).count()
        
        article_data = ArticleWithStats(
            id=article.id,
            title=article.title,
            content=article.content,
            tags=article.tags,
            generated=article.generated,
            timestamp=article.timestamp,
            author_id=article.author_id,
            author=article.author,
            views_count=views_count,
            likes_count=likes_count
        )
        articles_with_stats.append(article_data)
    
    return articles_with_stats

@app.post("/articles/", response_model=ArticleResponse)
async def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_article = Article(
        title=article.title,
        content=article.content,
        tags=article.tags,
        generated=article.generated,
        author_id=current_user.id
    )
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return db_article

@app.get("/articles/{article_id}", response_model=ArticleWithStats)
async def get_article(
    article_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get stats
    views_count = db.query(View).filter(View.article_id == article_id).count()
    likes_count = db.query(Like).filter(Like.article_id == article_id).count()
    
    return ArticleWithStats(
        id=article.id,
        title=article.title,
        content=article.content,
        tags=article.tags,
        generated=article.generated,
        timestamp=article.timestamp,
        author_id=article.author_id,
        author=article.author,
        views_count=views_count,
        likes_count=likes_count
    )

@app.post("/articles/{article_id}/view")
async def record_view(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Check if article exists
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Record view
    user_id = current_user.id if current_user else None
    new_view = View(user_id=user_id, article_id=article_id)
    db.add(new_view)
    db.commit()
    
    return {"message": "View recorded"}

@app.post("/articles/{article_id}/like")
async def like_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if article exists
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if already liked
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.article_id == article_id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="Article already liked")
    
    # Create like
    new_like = Like(user_id=current_user.id, article_id=article_id)
    db.add(new_like)
    db.commit()
    
    likes_count = db.query(Like).filter(Like.article_id == article_id).count()
    
    return {"message": "Article liked successfully", "likes_count": likes_count}

# ==================== AI ROUTES ====================

@app.post("/generate/")
async def generate_article_endpoint(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = ai_services.generate_article(request.title)
        return {"content": result["article"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Article generation failed: {str(e)}"
        )

@app.post("/predict/")
async def predict_next_words(
    request: PredictRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Generate multiple predictions and return them as a list
        predictions = []
        for _ in range(5):  # Generate 5 predictions
            result = ai_services.generate_next_words(
                seed_text=request.seed_text,
                next_words=1,
                temperature=0.8
            )
            # Extract just the new word
            new_word = result.split()[-1] if result != request.seed_text else ""
            if new_word and new_word not in predictions:
                predictions.append(new_word)
        
        return {"predictions": predictions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Next word prediction failed: {str(e)}"
        )

@app.get("/recommendations/")
async def get_recommendations(title: str, top_k: int = 5):
    try:
        recommendations = ai_services.get_similar_articles(title, top_k)
        # Format the recommendations to match frontend expectations
        formatted_recommendations = []
        for i, rec in enumerate(recommendations):
            formatted_recommendations.append({
                "id": i + 1,
                "title": rec.get("clean_title", ""),
                "content": rec.get("clean_text", "")
            })
        return formatted_recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}"
        )

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models": ai_services.is_available()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)