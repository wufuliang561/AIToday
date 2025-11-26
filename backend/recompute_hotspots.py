import argparse
import asyncio
import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.db.session import SessionLocal
from app.models.item import RawItem
from app.services.clustering import ClusteringService
from app.models.hotspot import Hotspot


logger = logging.getLogger("recompute_hotspots")


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def build_clusters(items: List[RawItem], svc: ClusteringService) -> List[Dict[str, Any]]:
    """
    按当前聚类规则构造簇，但不落库，用于提前打印详情。
    """
    vectorized = []
    for item in items:
        vector = svc._vector_from_item(item)  # 复用已有向量转换逻辑
        if not vector:
            logger.info("Skip item %s: no embedding", item.id or item.source_id)
            continue
        vectorized.append((item, vector))

    clusters: List[Dict[str, Any]] = []
    for item, vector in sorted(
        vectorized,
        key=lambda pair: pair[0].heat_score or 0,
        reverse=True,
    ):
        matched_cluster = None
        for cluster in clusters:
            similarity = svc._cosine_similarity(vector, cluster["centroid"])
            if similarity >= svc.similarity_threshold:
                matched_cluster = cluster
                break

        if matched_cluster:
            matched_cluster["members"].append(item)
            matched_cluster["vectors"].append(vector)
            matched_cluster["centroid"] = svc._average_vector(matched_cluster["vectors"])
        else:
            clusters.append(
                {
                    "members": [item],
                    "vectors": [vector],
                    "centroid": vector,
                }
            )

    return clusters


async def recompute_hotspots(hours: int, top: int, dry_run: bool, verbose: bool):
    setup_logging(verbose)
    db = SessionLocal()
    svc = ClusteringService(db)
    since = datetime.utcnow() - timedelta(hours=hours)
    try:
        candidates: List[RawItem] = (
            db.query(RawItem)
            .filter(RawItem.cluster_id == None, RawItem.published_at >= since)
            .all()
        )
        logger.info(
            "Loaded %d unclustered items within last %s hours",
            len(candidates),
            hours,
        )
        if not candidates:
            return

        source_breakdown = Counter(item.source_platform or "unknown" for item in candidates)
        logger.info(
            "Source breakdown: %s",
            ", ".join(f"{k}={v}" for k, v in source_breakdown.items()),
        )

        clusters = build_clusters(candidates, svc)
        eligible = [
            cluster for cluster in clusters if len(cluster["members"]) >= svc.min_cluster_size
        ]
        eligible_sorted = sorted(
            eligible,
            key=lambda c: len(c["members"]),
            reverse=True,
        )

        logger.info(
            "Built %d clusters, %d eligible (size >= %d)",
            len(clusters),
            len(eligible_sorted),
            svc.min_cluster_size,
        )

        preview_limit = min(top, len(eligible_sorted))
        for idx, cluster in enumerate(eligible_sorted[:preview_limit], start=1):
            members = cluster["members"]
            sources = Counter(item.source_platform or "unknown" for item in members)
            titles = [
                item.title_cn or item.original_title
                for item in members
                if item.title_cn or item.original_title
            ]
            logger.info(
                "[Cluster %d] size=%d sources=%s titles=%s",
                idx,
                len(members),
                ", ".join(f"{k}:{v}" for k, v in sources.items()) or "unknown",
                " | ".join(titles[:3]),
            )
            if verbose:
                for item in members:
                    logger.debug(
                        "  - id=%s source=%s heat=%.2f title=%s",
                        item.id,
                        item.source_platform,
                        item.heat_score or 0.0,
                        item.title_cn or item.original_title,
                    )

        if dry_run:
            logger.info("Dry-run enabled; skip hotspot creation.")
            return

        logger.info("Creating up to %d hotspots from eligible clusters...", preview_limit)
        for cluster in eligible_sorted[:preview_limit]:
            await svc._create_hotspot(cluster["members"])

        new_hotspots = (
            db.query(Hotspot).filter(Hotspot.created_at >= since).count()
        )
        logger.info(
            "Hotspot recompute completed. Hotspots in the window (>= %sh): %d",
            hours,
            new_hotspots,
        )
    finally:
        db.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Recompute hotspots with verbose clustering logs."
    )
    parser.add_argument("--hours", type=int, default=24, help="Look back window in hours.")
    parser.add_argument("--top", type=int, default=10, help="Max hotspots to create.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only log clustering result without creating hotspots.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable debug logs for cluster members."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(recompute_hotspots(args.hours, args.top, args.dry_run, args.verbose))
