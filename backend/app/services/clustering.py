from typing import List
from sqlalchemy.orm import Session
from app.models.item import RawItem
from app.models.hotspot import Hotspot
from app.services.processor import Processor
from datetime import datetime, timedelta

class ClusteringService:
    def __init__(self, db: Session):
        self.db = db
        self.processor = Processor()

    async def cluster_items(self):
        """
        Cluster unclustered items into hotspots.
        Simple logic: Group by similarity (mocked here) or just high heat items.
        For this MVP, we will treat high heat items as hotspots themselves or group by simple keyword matching if possible.
        
        Better approach for MVP:
        1. Get unclustered items from last 24h.
        2. If an item has very high heat (>80), it becomes a candidate for a hotspot.
        3. Use LLM to generate a hotspot title from these high heat items.
        """
        
        # Get unclustered items from last 24h
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        items = self.db.query(RawItem).filter(
            RawItem.cluster_id == None,
            RawItem.published_at >= time_threshold
        ).all()

        # Simple Clustering Logic for MVP:
        # 1. Find items with heat_score > 80
        # 2. Create a hotspot for each (or group if we had vector search)
        
        for item in items:
            if item.heat_score > 0:
                # Create a new hotspot
                hotspot = Hotspot(
                    title=item.title_cn or item.original_title, # Use item title as hotspot title for now
                    summary=item.summary_cn,
                    total_heat_score=item.heat_score
                )
                self.db.add(hotspot)
                self.db.commit()
                self.db.refresh(hotspot)
                
                # Link item to hotspot
                item.cluster_id = hotspot.id
                self.db.commit()
                
        # TODO: Implement vector-based clustering for better aggregation
