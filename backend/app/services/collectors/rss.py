import feedparser
import html
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from app.services.collectors.base import BaseCollector
from app.models.item import RawItem
from app.core.config import load_sources_config

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
            feed_type = feed_config.get("type", "rss")
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
                
                published = self._parse_published(entry)

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

                item: Optional[RawItem] = None
                if feed_type == "rss_twitter":
                    item = self._build_twitter_item(entry, published, base_heat, category_override)
                else:
                    item = self._build_default_item(entry, published, base_heat, category_override)

                if item:
                    items.append(item)
                
        logger.info(f"RSS collection complete. Total items: {len(items)}")
        return items

    def _parse_published(self, entry) -> datetime:
        """解析 RSS 条目的发布时间，若缺失则回退到当前时间。"""
        if hasattr(entry, "published_parsed"):
            return datetime(*entry.published_parsed[:6])
        if hasattr(entry, "updated_parsed"):
            return datetime(*entry.updated_parsed[:6])
        return datetime.utcnow()

    def _build_default_item(self, entry, published: datetime, base_heat: float, category_override: Optional[str]) -> RawItem:
        """构建常规 RSS 条目的 RawItem。"""
        return RawItem(
            source_platform="rss",
            source_id=entry.id if hasattr(entry, "id") else entry.link,
            original_title=getattr(entry, "title", ""),
            original_text=getattr(entry, "summary", "") if hasattr(entry, "summary") else "",
            title_cn="", # 将由 LLM 填充
            url=getattr(entry, "link", ""),
            published_at=published,
            category=category_override,
            heat_score=base_heat # RSS 的默认分数，可配置
        )

    def _build_twitter_item(
        self,
        entry,
        published: datetime,
        base_heat: float,
        category_override: Optional[str],
    ) -> RawItem:
        """针对 Twitter RSS，将描述中的 HTML 提取为纯文本并补齐作者。"""
        description_html = getattr(entry, "description", "")
        tweet_text = self._extract_text_from_html(description_html)

        title = getattr(entry, "title", "") or ((tweet_text[:50] + "...") if tweet_text else "")
        source_id = getattr(entry, "id", None) or getattr(entry, "link", "")
        author = getattr(entry, "dc_creator", None) or getattr(entry, "author", None)

        return RawItem(
            source_platform="x",  # 统一用推文提示词
            source_id=source_id,
            original_title=title or "untitled tweet",
            original_text=tweet_text or title,
            title_cn="", # 由 LLM 填充
            url=getattr(entry, "link", ""),
            published_at=published,
            category=category_override,
            heat_score=base_heat,
            author_name=author,
        )

    def _extract_text_from_html(self, html_content: str) -> str:
        """从 RSS 描述中剥离脚本/标签，保留锚文本形成纯文本。"""
        if not html_content:
            return ""

        text = html.unescape(html_content)
        text = re.sub(r"<script.*?>.*?</script>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.S | re.I)
        text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        text = re.sub(r"</p>", "\n", text, flags=re.I)
        text = re.sub(r"<.*?>", " ", text, flags=re.S)
        text = re.sub(r"\s+", " ", text).strip()
        return text
