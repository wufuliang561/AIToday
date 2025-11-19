from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class RawItem(Base):
    __tablename__ = "raw_items"

    id = Column(Integer, primary_key=True, index=True)
    source_platform = Column(String(20), nullable=False)  # 'youtube', 'x', 'reddit', 'rss'
    source_id = Column(String(255), unique=True, nullable=False)
    
    # Content
    original_title = Column(Text, nullable=False)
    original_text = Column(Text)
    title_cn = Column(Text, nullable=False)
    summary_cn = Column(Text)
    url = Column(Text, nullable=False)
    
    # Metadata
    category = Column(String(50))
    author_name = Column(String(100))
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Algorithm fields
    heat_score = Column(Float, default=0.0)
    cluster_id = Column(Integer, ForeignKey("hotspots.id"), nullable=True)
