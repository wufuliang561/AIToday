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
        将未聚类的条目聚类成热点。
        简单逻辑：按相似度分组（此处为模拟）或仅按高热度条目分组。
        对于此 MVP，我们将高热度条目视为热点本身，或者如果可能的话，按简单的关键字匹配进行分组。
        
        MVP 的更好方法：
        1. 获取过去 24 小时内未聚类的条目。
        2. 如果一个条目的热度非常高（>80），它就成为热点的候选者。
        3. 使用 LLM 从这些高热度条目生成热点标题。
        """
        
        # 获取过去 24 小时内未聚类的条目
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        items = self.db.query(RawItem).filter(
            RawItem.cluster_id == None,
            RawItem.published_at >= time_threshold
        ).all()

        # MVP 的简单聚类逻辑：
        # 1. 查找 heat_score > 80 的条目
        # 2. 为每个条目创建一个热点（如果我们有向量搜索，则进行分组）
        
        for item in items:
            if item.heat_score > 0:
                # 创建一个新的热点
                hotspot = Hotspot(
                    title=item.title_cn or item.original_title, # 暂时使用条目标题作为热点标题
                    summary=item.summary_cn,
                    total_heat_score=item.heat_score
                )
                self.db.add(hotspot)
                self.db.commit()
                self.db.refresh(hotspot)
                
                # 将条目链接到热点
                item.cluster_id = hotspot.id
                self.db.commit()
                
        # TODO: 实现基于向量的聚类以获得更好的聚合效果
