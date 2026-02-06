from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.db.database import get_db
from app.db.repositories import TokenUsageRepository

app = FastAPI(title="Florida Man API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Florida Man API"}


@app.get("/api/token-usage/stats")
def get_usage_stats(db: Session = Depends(get_db)):
    """Get aggregate token usage statistics"""
    repo = TokenUsageRepository(db)
    return repo.get_stats()


@app.get("/api/token-usage/history")
def get_usage_history(limit: int = 100, db: Session = Depends(get_db)):
    """Get recent token usage history"""
    repo = TokenUsageRepository(db)
    return repo.get_recent(limit)
