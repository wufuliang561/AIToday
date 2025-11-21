import logging
import praw
from datetime import datetime
from typing import List
from app.services.collectors.base import BaseCollector
from app.models.item import RawItem
from app.core.config import settings, load_sources_config

logger = logging.getLogger(__name__)

class RedditCollector(BaseCollector):
    def __init__(self):
        self.config = load_sources_config()
        self.client_id = settings.REDDIT_CLIENT_ID if hasattr(settings, 'REDDIT_CLIENT_ID') else ""
        self.client_secret = settings.REDDIT_CLIENT_SECRET if hasattr(settings, 'REDDIT_CLIENT_SECRET') else ""
        self.user_agent = settings.REDDIT_USER_AGENT if hasattr(settings, 'REDDIT_USER_AGENT') else "AIToday/0.1.0"
        self.username = getattr(settings, 'REDDIT_USERNAME', "")
        self.password = getattr(settings, 'REDDIT_PASSWORD', "")

    async def collect(self) -> List[RawItem]:
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit credentials missing; skipping Reddit collection")
            return []

        praw_kwargs = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "user_agent": self.user_agent,
        }
        if self.username and self.password:
            praw_kwargs["username"] = self.username
            praw_kwargs["password"] = self.password
            logger.info("Using script authentication for Reddit (user=%s)", self.username)
        else:
            logger.warning("Reddit username/password not provided; using application-only auth")

        reddit = praw.Reddit(**praw_kwargs)
        
        items = []
        subreddits = self.config.get("reddit", {}).get("subreddits", [])
        
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                # 获取过去 24 小时的热门帖子
                for submission in subreddit.top(time_filter="day", limit=10):
                    
                    # 热度评分：S_rd = min(100, Upvotes*0.5 + Comments*1)
                    heat_score = min(100.0, (submission.score * 0.5) + (submission.num_comments * 1))

                    raw_item = RawItem(
                        source_platform="reddit",
                        source_id=submission.id,
                        original_title=submission.title,
                        original_text=submission.selftext,
                        title_cn="", # 将由 LLM 填充
                        url=f"https://www.reddit.com{submission.permalink}",
                        published_at=datetime.utcfromtimestamp(submission.created_utc),
                        heat_score=heat_score,
                        author_name=str(submission.author)
                    )
                    items.append(raw_item)
            except Exception as e:
                logger.exception("Error collecting from subreddit %s", subreddit_name)
                
        return items
