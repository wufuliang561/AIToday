from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import Dict, List
from app.services.collectors.base import BaseCollector
from app.models.item import RawItem
from app.core.config import settings, load_sources_config
import logging

logger = logging.getLogger(__name__)

class YouTubeCollector(BaseCollector):
    def __init__(self):
        self.config = load_sources_config()
        youtube_config = self.config.get("youtube", {})
        self.channels = [c for c in youtube_config.get("channels", []) if c.get("enabled", True)]
        self.max_results = max(1, youtube_config.get("max_results", 5))
        self.lookback_hours = max(1, youtube_config.get("lookback_hours", 12))
        self.stats_batch_size = min(50, max(1, youtube_config.get("stats_batch_size", 25)))
        raw_keys = []
        # 支持 sources.yaml 的 youtube.api_keys 列表以及顶层 api_keys.youtube
        config_keys = youtube_config.get("api_keys", [])
        if isinstance(config_keys, str):
            config_keys = [config_keys]
        raw_keys.extend(config_keys)
        api_keys_root = self.config.get("api_keys", {})
        if isinstance(api_keys_root.get("youtube"), str):
            raw_keys.append(api_keys_root.get("youtube"))
        # 环境变量单 key
        if getattr(settings, "YOUTUBE_API_KEY", ""):
            raw_keys.append(settings.YOUTUBE_API_KEY)
        # 去重并过滤空值
        self.api_keys = [k for i, k in enumerate(raw_keys) if k and k not in raw_keys[:i]]
        self.api_key_index = 0

    def _current_api_key(self) -> str:
        if not self.api_keys:
            return ""
        return self.api_keys[self.api_key_index]

    def _rotate_api_key(self) -> bool:
        if not self.api_keys or len(self.api_keys) == 1:
            return False
        old_key = self._current_api_key()
        self.api_key_index = (self.api_key_index + 1) % len(self.api_keys)
        logger.warning(
            "Rotating YouTube API key from index %d to %d",
            (self.api_key_index - 1) % len(self.api_keys),
            self.api_key_index,
        )
        return self._current_api_key() != old_key

    def _build_client(self):
        api_key = self._current_api_key()
        if not api_key:
            return None
        return build("youtube", "v3", developerKey=api_key)

    @staticmethod
    def _is_quota_exceeded(error: HttpError) -> bool:
        try:
            reason = error.error_details[0]["reason"]  # type: ignore
            return reason == "quotaExceeded"
        except Exception:
            return False

    async def collect(self) -> List[RawItem]:
        logger.info("Starting YouTube collection...")
        if not self.api_keys:
            logger.warning("No YouTube API keys configured.")
            return []

        youtube = self._build_client()
        items = []
        if not self.channels:
            logger.info("No YouTube channels configured.")
            return []

        logger.info(
            "YouTube collector configured with %s channels, lookback=%sh, max_results=%s",
            len(self.channels),
            self.lookback_hours,
            self.max_results,
        )

        time_threshold = (datetime.utcnow() - timedelta(hours=self.lookback_hours)).isoformat() + "Z"

        for channel in self.channels:
            channel_id = channel.get("id")
            
            for attempt in range(len(self.api_keys) or 1):
                try:
                    request = youtube.search().list(
                        part="snippet",
                        channelId=channel_id,
                        order="date",
                        publishedAfter=time_threshold,
                        type="video",
                        maxResults=self.max_results
                    )
                    response = request.execute()
                    
                    channel_items = response.get("items", [])
                    logger.info(f"Collected {len(channel_items)} videos from channel {channel.get('name')} ({channel_id}) with key#{self.api_key_index}")
                    break
                except HttpError as e:
                    if self._is_quota_exceeded(e) and self._rotate_api_key():
                        youtube = self._build_client()
                        logger.warning("Quota exceeded, switched API key to index %d", self.api_key_index)
                        continue
                    logger.error(f"Error collecting from channel {channel.get('name')} ({channel_id}): {e}")
                    channel_items = []
                    break
                except Exception as e:
                    logger.error(f"Error collecting from channel {channel.get('name')} ({channel_id}): {e}")
                    channel_items = []
                    break
            
            video_ids = [item["id"].get("videoId") for item in channel_items if item.get("id", {}).get("videoId")]
            stats_map = self._fetch_video_stats(youtube, video_ids)

            for item in channel_items:
                video_id = item["id"].get("videoId")
                if not video_id:
                    continue
                snippet = item["snippet"]
                stats = stats_map.get(video_id, {})
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

    def _fetch_video_stats(self, youtube, video_ids: List[str]) -> Dict[str, Dict[str, str]]:
        """Batch fetch statistics for a list of video IDs."""
        stats_map: Dict[str, Dict[str, str]] = {}
        if not video_ids:
            return stats_map

        for i in range(0, len(video_ids), self.stats_batch_size):
            chunk = video_ids[i:i + self.stats_batch_size]
            try:
                stats_request = youtube.videos().list(
                    part="statistics",
                    id=",".join(chunk)
                )
                stats_response = stats_request.execute()
            except Exception as e:
                logger.error(f"Error fetching video stats for chunk starting with {chunk[0]}: {e}")
                continue

            for stats_item in stats_response.get("items", []):
                stats_map[stats_item["id"]] = stats_item.get("statistics", {})

        return stats_map
