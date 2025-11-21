from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import SessionLocal
from app.models.item import RawItem
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()

# 依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FeedItem(BaseModel):
    id: int
    title: str
    source: str
    url: str
    publishedAt: str
    author: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None

    class Config:
        orm_mode = True

@router.get("/", response_model=List[FeedItem])
def read_feed(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # 只获取过去 24 小时内的内容
    since = datetime.utcnow() - timedelta(hours=24)
    items = db.query(RawItem).filter(
        RawItem.cluster_id == None,
        RawItem.published_at >= since
    ).order_by(RawItem.published_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for item in items:
        result.append(FeedItem(
            id=item.id,
            title=item.title_cn or item.original_title,
            source=item.source_platform,
            url=item.url,
            publishedAt=item.published_at.strftime("%Y-%m-%d %H:%M") if item.published_at else "",
            author=item.author_name,
            category=item.category,
            summary=item.summary_cn
        ))
    return result
