from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from pydantic import BaseModel
from app.services.headline_service import HeadlineService

router = APIRouter()


class GuessRequest(BaseModel):
    headline_id: int
    guess: bool


@router.get("/headline")
async def get_random_headline(db: Session = Depends(get_db)):
    """Get a random headline for the game"""
    service = HeadlineService(db)
    headline = service.get_game_headline()
    if not headline:
        raise HTTPException(status_code=404, detail="No headlines available")

    return headline

    # return {
    #     "id": 1,
    #     "text": "Florida man arrested for training attack squirrels.",
    #     "is_real": None  # Frontend shouldn't see this until user guesses
    # }


@router.post("/guess")
async def submit_guess(request: GuessRequest, db: Session = Depends(get_db)):

    """Submit a guess and get feedback"""
    service = HeadlineService(db)
    result = service.check_guess(request.headline_id, request.guess)

    if not result:
        raise HTTPException(status_code=404, detail="Headline not found")

    return result
