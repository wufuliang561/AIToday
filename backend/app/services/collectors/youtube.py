from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List
from app.services.collectors.base import BaseCollector
from app.models.item import RawItem
from app.core.config import settings, load_sources_config
import logging

logger = logging.getLogger(__name__)

class YouTubeCollector(BaseCollector):
    def __init__(self):
        self.config = load_sources_config()
        self.api_key = settings.YOUTUBE_API_KEY if hasattr(settings, 'YOUTUBE_API_KEY') else "" 
        # 注意：如果不存在，我们需要将 YOUTUBE_API_KEY 添加到设置中，
        # 或者暂时只使用占位符。

    async def collect(self) -> List[RawItem]:
        logger.info("Starting YouTube collection...")
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not set.")
            return []

        youtube = build("youtube", "v3", developerKey=self.api_key)
        items = []
        channels = self.config.get("youtube", {}).get("channels", [])
        logger.info(f"Found {len(channels)} channels to process.")
        
        # 计算“今天”的时间（为简单起见，取过去 24 小时）
        time_threshold = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"

        for channel in channels:
            channel_id = channel.get("id")
            
            try:
                request = youtube.search().list(
                    part="snippet",
                    channelId=channel_id,
                    order="date",
                    publishedAfter=time_threshold,
                    type="video",
                    maxResults=10
                )
                response = request.execute()
                
                channel_items = response.get("items", [])
                logger.info(f"Collected {len(channel_items)} videos from channel {channel.get('name')} ({channel_id})")
            except Exception as e:
                logger.error(f"Error collecting from channel {channel.get('name')} ({channel_id}): {e}")
                continue
            
            for item in response.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                
                # 获取热度评分的统计数据
                stats_request = youtube.videos().list(
                    part="statistics",
                    id=video_id
                )
                stats_response = stats_request.execute()
                stats = stats_response["items"][0]["statistics"]
                view_count = int(stats.get("viewCount", 0))
                
                # 计算热度评分（来自 PRD 的简单算法）
                # S_yt = min(100, (Views / 10000) * 2)
                heat_score = min(100.0, (view_count / 10000) * 2)

                raw_item = RawItem(
                    source_platform="youtube",
                    source_id=video_id,
                    original_title=snippet["title"],
                    original_text=snippet["description"],
                    title_cn="", # 将由 LLM 填充
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                    heat_score=heat_score,
                    author_name=snippet["channelTitle"]
                )
                items.append(raw_item)
                
        logger.info(f"YouTube collection complete. Total items: {len(items)}")
        return items
