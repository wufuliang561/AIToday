import tweepy
from datetime import datetime, timedelta
from typing import List
from app.services.collectors.base import BaseCollector
from app.models.item import RawItem
from app.core.config import settings, load_sources_config

class TwitterCollector(BaseCollector):
    def __init__(self):
        self.config = load_sources_config()
        self.bearer_token = settings.TWITTER_BEARER_TOKEN if hasattr(settings, 'TWITTER_BEARER_TOKEN') else ""

    async def collect(self) -> List[RawItem]:
        if not self.bearer_token:
            print("Warning: TWITTER_BEARER_TOKEN not set.")
            return []

        client = tweepy.Client(bearer_token=self.bearer_token)
        items = []
        users = self.config.get("twitter", {}).get("users", [])
        
        # Time threshold: last 24 hours
        start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"

        for user in users:
            user_id = user.get("id")
            
            try:
                # Get tweets
                response = client.get_users_tweets(
                    id=user_id,
                    max_results=10,
                    start_time=start_time,
                    tweet_fields=["created_at", "public_metrics", "text"],
                    exclude=["retweets", "replies"]
                )
                
                if not response.data:
                    continue

                for tweet in response.data:
                    metrics = tweet.public_metrics
                    likes = metrics.get("like_count", 0)
                    retweets = metrics.get("retweet_count", 0)
                    
                    # Heat score: S_x = min(100, Likes/50 + Retweets*2)
                    heat_score = min(100.0, (likes / 50) + (retweets * 2))

                    raw_item = RawItem(
                        source_platform="x",
                        source_id=str(tweet.id),
                        original_title=tweet.text[:50] + "...", # Use first 50 chars as title
                        original_text=tweet.text,
                        title_cn="", # To be filled by LLM
                        summary_cn="", # To be filled by LLM
                        url=f"https://twitter.com/{user.get('username')}/status/{tweet.id}",
                        published_at=tweet.created_at,
                        heat_score=heat_score,
                        author_name=user.get("username")
                    )
                    items.append(raw_item)
            except Exception as e:
                print(f"Error collecting tweets for user {user_id}: {e}")
                
        return items
