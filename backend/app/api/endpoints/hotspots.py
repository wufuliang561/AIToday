from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import SessionLocal
from app.models.hotspot import Hotspot
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class HotspotResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    score: float
    itemsCount: int
    time: str

    class Config:
        orm_mode = True

@router.get("/", response_model=List[HotspotResponse])
def read_hotspots(db: Session = Depends(get_db)):
    hotspots = db.query(Hotspot).order_by(Hotspot.total_heat_score.desc()).limit(10).all()
    
    result = []
    for h in hotspots:
        result.append(HotspotResponse(
            id=h.id,
            title=h.title,
            summary=h.summary,
            score=h.total_heat_score or 0.0,
            itemsCount=len(h.items),
            time=h.created_at.strftime("%Y-%m-%d %H:%M") if h.created_at else ""
        ))
    return result
