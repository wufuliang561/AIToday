import feedparser
from datetime import datetime, timedelta
from typing import List, Optional
from app.services.collectors.base import BaseCollector
from app.models.item import RawItem
from app.core.config import load_sources_config
import logging

logger = logging.getLogger(__name__)

class RSSCollector(BaseCollector):
    def __init__(self):
        self.config = load_sources_config()

    async def collect(self) -> List[RawItem]:
        logger.info("Starting RSS collection...")
        items = []
        feeds = self.config.get("rss", {}).get("feeds", [])
        logger.info(f"Found {len(feeds)} RSS feeds to process.")
        
        for feed_config in feeds:
            url = feed_config.get("url")
            feed_name = feed_config.get("name", url)
            max_age_hours: Optional[int] = feed_config.get("max_age_hours")
            base_heat = float(feed_config.get("base_heat", 60.0))
            category_override = feed_config.get("category")
            try:
                feed = feedparser.parse(url)
                logger.info(
                    "Collected %d entries from RSS feed: %s (%s)",
                    len(feed.entries),
                    feed_name,
                    url,
                )
            except Exception as e:
                logger.error("Error parsing RSS feed %s (%s): %s", feed_name, url, e)
                continue
            
            for entry in feed.entries:
                # 基本的重复数据删除检查应该在数据库级别进行，
                # 但在这里我们只是创建对象。
                
                published = None
                if hasattr(entry, "published_parsed"):
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed"):
                    published = datetime(*entry.updated_parsed[:6])
                else:
                    published = datetime.utcnow()

                if max_age_hours:
                    threshold = datetime.utcnow() - timedelta(hours=max_age_hours)
                    if published < threshold:
                        logger.debug(
                            "Skipping RSS entry '%s' from %s (published %s older than %sh)",
                            getattr(entry, "title", "Untitled"),
                            feed_name,
                            published,
                            max_age_hours,
                        )
                        continue

                item = RawItem(
                    source_platform="rss",
                    source_id=entry.id if hasattr(entry, "id") else entry.link,
                    original_title=entry.title,
                    original_text=entry.summary if hasattr(entry, "summary") else "",
                    title_cn="", # 将由 LLM 填充
                    url=entry.link,
                    published_at=published,
                    category=category_override,
                    heat_score=base_heat # RSS 的默认分数，可配置
                )
                items.append(item)
                
        logger.info(f"RSS collection complete. Total items: {len(items)}")
        return items
