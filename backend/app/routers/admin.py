from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

router = APIRouter()


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    # TODO: Implement stats query
    return {
        "total_headlines": 0,
        "real_headlines": 0,
        "fake_headlines": 0
    }


@router.post("/scrape")
async def trigger_scrape():
    """Manually trigger scraping job"""
    # TODO: Implement scraper trigger
    return {"message": "Scrape job queued"}
