from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db

router = APIRouter()


@router.get("/headline")
async def get_random_headline(db: Session = Depends(get_db)):
    """Get a random headline for the game"""
    # TODO: Implement random headline selection
    return {
        "id": 1,
        "text": "Florida man arrested for training attack squirrels.",
        "is_real": None  # Frontend shouldn't see this until user guesses
    }


@router.post("/guess")
async def submit_guess(
    headline_id: int, guess: bool, db: Session = Depends(get_db)
):
    """Submit a guess and get feedback"""
    # TODO: Implement guess validation
    return {
        "correct": True,
        "was_real": True,
        "source_url": "https://floridaman.com/example"
    }
