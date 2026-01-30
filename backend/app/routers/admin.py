from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.services.headline_service import HeadlineService

router = APIRouter()


class AddHeadlineRequest(BaseModel):
    text: str
    is_real: bool
    source_url: Optional[str] = None


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    service = HeadlineService(db)
    return service.get_stats()


@router.post("/headline")
async def add_headline(
    request: AddHeadlineRequest,
    db: Session = Depends(get_db)
):
    """Manually add a headline"""
    service = HeadlineService(db)

    try:
        headline = service.add_headline(
            text=request.text,
            is_real=request.is_real,
            source_url=request.source_url
        )
        return {
            "id": headline.id,
            "text": headline.text,
            "is_real": headline.is_real,
            "message": "Headline added successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scrape")
async def trigger_scrape():
    """Manually trigger scraping job (placeholder for now)"""
    # TODO: Implement scraper trigger via agents
    return {"message": "Scrape job queued (not implemented yet)"}
