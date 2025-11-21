import logging
import tweepy
from datetime import datetime, timedelta
from typing import List
from app.services.collectors.base import BaseCollector
from app.models.item import RawItem
from app.core.config import settings, load_sources_config

logger = logging.getLogger(__name__)

class TwitterCollector(BaseCollector):
    def __init__(self):
        self.config = load_sources_config()
        self.bearer_token = settings.TWITTER_BEARER_TOKEN if hasattr(settings, 'TWITTER_BEARER_TOKEN') else ""

    async def collect(self) -> List[RawItem]:
        if not self.bearer_token:
            logger.warning("TWITTER_BEARER_TOKEN not set; skipping Twitter collection")
            return []

        client = tweepy.Client(bearer_token=self.bearer_token)
        items = []
        users = self.config.get("twitter", {}).get("users", [])
        
        # 时间阈值：过去 24 小时
        start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"

        for user in users:
            user_id = user.get("id")
            
            try:
                # 获取推文
                response = client.get_users_tweets(
                    id=user_id,
                    max_results=10,
                    start_time=start_time,
                    tweet_fields=["created_at", "public_metrics", "text"],
                    exclude=["retweets", "replies"]
                )
                
                if not response.data:
                    logger.info("No tweets found for user %s in last 24h", user.get("username"))
                    continue

                for tweet in response.data:
                    metrics = tweet.public_metrics
                    likes = metrics.get("like_count", 0)
                    retweets = metrics.get("retweet_count", 0)
                    
                    # 热度评分：S_x = min(100, Likes/50 + Retweets*2)
                    heat_score = min(100.0, (likes / 50) + (retweets * 2))

                    raw_item = RawItem(
                        source_platform="x",
                        source_id=str(tweet.id),
                        original_title=tweet.text[:50] + "...", # 使用前 50 个字符作为标题
                        original_text=tweet.text,
                        title_cn="", # 将由 LLM 填充
                        summary_cn="", # 将由 LLM 填充
                        url=f"https://twitter.com/{user.get('username')}/status/{tweet.id}",
                        published_at=tweet.created_at,
                        heat_score=heat_score,
                        author_name=user.get("username")
                    )
                    items.append(raw_item)
            except Exception as e:
                logger.exception("Error collecting tweets for user %s", user_id)
                
        return items
