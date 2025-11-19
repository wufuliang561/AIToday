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
        # Note: We need to add YOUTUBE_API_KEY to settings if not present, 
        # or just use a placeholder for now.

    async def collect(self) -> List[RawItem]:
        logger.info("Starting YouTube collection...")
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not set.")
            return []

        youtube = build("youtube", "v3", developerKey=self.api_key)
        items = []
        channels = self.config.get("youtube", {}).get("channels", [])
        logger.info(f"Found {len(channels)} channels to process.")
        
        # Calculate time for "today" (last 24 hours for simplicity)
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
                
                # Get statistics for heat score
                stats_request = youtube.videos().list(
                    part="statistics",
                    id=video_id
                )
                stats_response = stats_request.execute()
                stats = stats_response["items"][0]["statistics"]
                view_count = int(stats.get("viewCount", 0))
                
                # Calculate heat score (Simple algorithm from PRD)
                # S_yt = min(100, (Views / 10000) * 2)
                heat_score = min(100.0, (view_count / 10000) * 2)

                raw_item = RawItem(
                    source_platform="youtube",
                    source_id=video_id,
                    original_title=snippet["title"],
                    original_text=snippet["description"],
                    title_cn="", # To be filled by LLM
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                    heat_score=heat_score,
                    author_name=snippet["channelTitle"]
                )
                items.append(raw_item)
                
        logger.info(f"YouTube collection complete. Total items: {len(items)}")
        return items
