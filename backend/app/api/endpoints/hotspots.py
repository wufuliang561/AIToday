from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import SessionLocal
from app.models.hotspot import Hotspot
from pydantic import BaseModel
from datetime import datetime, timedelta

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

class HotspotItem(BaseModel):
    id: int
    title: str
    url: str
    source: str
    publishedAt: str
    summary: Optional[str] = None
    author: Optional[str] = None

class HotspotDetail(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    score: int
    itemsCount: int
    time: str
    items: List[HotspotItem]

    class Config:
        orm_mode = True

@router.get("/", response_model=List[HotspotResponse])
def read_hotspots(db: Session = Depends(get_db)):
    # 只获取过去 24 小时内的热点
    since = datetime.utcnow() - timedelta(hours=24)
    hotspots = db.query(Hotspot).filter(
        Hotspot.created_at >= since
    ).order_by(Hotspot.total_heat_score.desc()).limit(10).all()
    
    result = []
    for h in hotspots:
        result.append(HotspotResponse(
            id=h.id,
            title=h.title,
            summary=h.summary,
            score=len(h.items),
            itemsCount=len(h.items),
            time=h.created_at.strftime("%Y-%m-%d %H:%M") if h.created_at else ""
        ))
    return result

@router.get("/{hotspot_id}", response_model=HotspotDetail)
def read_hotspot_detail(hotspot_id: int, db: Session = Depends(get_db)):
    hotspot = db.query(Hotspot).filter(Hotspot.id == hotspot_id).first()
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    items_sorted = sorted(
        hotspot.items,
        key=lambda i: i.published_at.timestamp() if i.published_at else 0,
        reverse=True,
    )

    detail_items = [
        HotspotItem(
            id=item.id,
            title=item.title_cn or item.original_title,
            url=item.url,
            source=item.source_platform,
            publishedAt=item.published_at.strftime("%Y-%m-%d %H:%M") if item.published_at else "",
            summary=item.summary_cn,
            author=item.author_name,
        )
        for item in items_sorted
    ]

    return HotspotDetail(
        id=hotspot.id,
        title=hotspot.title,
        summary=hotspot.summary,
        score=len(detail_items),
        itemsCount=len(detail_items),
        time=hotspot.created_at.strftime("%Y-%m-%d %H:%M") if hotspot.created_at else "",
        items=detail_items,
    )
