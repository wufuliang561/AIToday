import feedparser
from datetime import datetime
from typing import List
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
            try:
                feed = feedparser.parse(url)
                logger.info(f"Collected {len(feed.entries)} entries from RSS feed: {feed_config.get('name')} ({url})")
            except Exception as e:
                logger.error(f"Error parsing RSS feed {feed_config.get('name')} ({url}): {e}")
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

                item = RawItem(
                    source_platform="rss",
                    source_id=entry.id if hasattr(entry, "id") else entry.link,
                    original_title=entry.title,
                    original_text=entry.summary if hasattr(entry, "summary") else "",
                    title_cn="", # 将由 LLM 填充
                    url=entry.link,
                    published_at=published,
                    heat_score=60.0 # RSS 的默认分数
                )
                items.append(item)
                
        logger.info(f"RSS collection complete. Total items: {len(items)}")
        return items
