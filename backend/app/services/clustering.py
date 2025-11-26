import math
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.item import RawItem
from app.models.hotspot import Hotspot
from app.services.processor import Processor
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ClusteringService:
    def __init__(self, db: Session):
        self.db = db
        self.processor = Processor()
        self.similarity_threshold = 0.85
        self.min_cluster_size = 2

    async def cluster_items(self):
        """
        使用向量余弦相似度将条目聚为热点。
        取近 24 小时未归档的条目，按相似度聚簇后按簇大小排序，选前 5 个生成热点。
        """
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        items: List[RawItem] = self.db.query(RawItem).filter(
            RawItem.cluster_id == None,
            RawItem.published_at >= time_threshold
        ).all()

        if not items:
            logger.info("No items found for clustering window")
            return

        vectorized_items = []
        for item in items:
            vector = self._vector_from_item(item)
            if vector:
                vectorized_items.append((item, vector))

        clusters = []
        # 先按热度排序，热点标题更容易由高热度条目引领
        for item, vector in sorted(
            vectorized_items,
            key=lambda pair: pair[0].heat_score or 0,
            reverse=True
        ):
            matched_cluster = None
            for cluster in clusters:
                similarity = self._cosine_similarity(vector, cluster["centroid"])
                if similarity >= self.similarity_threshold:
                    matched_cluster = cluster
                    break

            if matched_cluster:
                matched_cluster["members"].append(item)
                matched_cluster["vectors"].append(vector)
                matched_cluster["centroid"] = self._average_vector(matched_cluster["vectors"])
            else:
                clusters.append({
                    "members": [item],
                    "vectors": [vector],
                    "centroid": vector
                })

        eligible_clusters = [
            cluster for cluster in clusters
            if len(cluster["members"]) >= self.min_cluster_size
        ]

        if not eligible_clusters:
            logger.info("No eligible clusters found for hotspot creation")
            return

        # 按簇大小排序，选前 5 个
        top_clusters = sorted(
            eligible_clusters,
            key=lambda c: len(c["members"]),
            reverse=True
        )[:5]

        for cluster in top_clusters:
            logger.info(
                "Creating hotspot from cluster with %d items",
                len(cluster["members"]),
            )
            await self._create_hotspot(cluster["members"])

    async def _create_hotspot(self, items: List[RawItem]):
        if not items:
            return

        title, summary = await self._generate_hotspot_text(items)
        total_heat = len(items)  # 以簇内条目数作为热点“热度”

        hotspot = Hotspot(
            title=title,
            summary=summary,
            total_heat_score=total_heat
        )
        self.db.add(hotspot)
        self.db.commit()
        self.db.refresh(hotspot)

        for item in items:
            item.cluster_id = hotspot.id
        self.db.commit()
        logger.info("Hotspot #%s created with %d items", hotspot.id, len(items))

    async def _generate_hotspot_text(self, items: List[RawItem]) -> Tuple[str, Optional[str]]:
        title_candidates = [item.title_cn or item.original_title for item in items if item.title_cn or item.original_title]
        fallback_title = title_candidates[0] if title_candidates else "AI 热点"
        fallback_summary = "；".join(title_candidates[:3])

        if not self.processor.client:
            return fallback_title, fallback_summary
        if not title_candidates:
            return fallback_title, fallback_summary

        prompt_lines = "\n".join(f"{idx+1}. {title}" for idx, title in enumerate(title_candidates))
        prompt = f"""
你是一名中文科技媒体编辑。请阅读以下资讯标题列表，生成一个简洁有力的中文热点标题以及一句中文概述。

资讯列表：
{prompt_lines}

输出格式：
Title: <合并后的标题>
Summary: <一句话概述>
"""

        try:
            response = self.processor.client.chat.completions.create(
                model=self.processor.model,
                messages=[
                    {"role": "system", "content": "你是一名科技资讯编辑，擅长概括热点事件。"},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content.strip()
            hotspot_title = fallback_title
            hotspot_summary = fallback_summary
            for line in content.split("\n"):
                if line.startswith("Title:"):
                    hotspot_title = line.replace("Title:", "").strip() or hotspot_title
                elif line.startswith("Summary:"):
                    hotspot_summary = line.replace("Summary:", "").strip() or hotspot_summary
            return hotspot_title, hotspot_summary
        except Exception as e:
            logger.exception("Error generating hotspot summary")
            return fallback_title, fallback_summary

    def _vector_from_item(self, item: RawItem) -> Optional[List[float]]:
        embedding = item.embedding
        if embedding is None:
            return None
        if isinstance(embedding, list):
            return embedding
        try:
            return list(embedding)
        except TypeError:
            logger.exception("Unable to convert embedding for item %s", item.id)
            return None

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _average_vector(self, vectors: List[List[float]]) -> List[float]:
        if not vectors:
            return []
        dimension = len(vectors[0])
        totals = [0.0] * dimension
        for vec in vectors:
            for idx in range(dimension):
                totals[idx] += vec[idx]
        return [value / len(vectors) for value in totals]
