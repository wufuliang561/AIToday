import httpx
import logging
from datetime import datetime, date
from typing import List, Optional
from app.services.collectors.base import BaseCollector
from app.models.item import RawItem
from app.core.config import load_sources_config

logger = logging.getLogger(__name__)

class HuggingFaceCollector(BaseCollector):
    def __init__(self):
        self.config = load_sources_config()
        self.base_url = "https://huggingface.co/api/daily_papers"

    async def collect(self) -> List[RawItem]:
        logger.info("Starting Hugging Face Daily Papers collection...")
        items = []
        
        # Get configuration
        hf_config = self.config.get("huggingface", {})
        # Default to today if not specified, but we can also look back if needed
        # For now, let's just fetch today's papers as per the daily nature of the source
        target_date = date.today()
        date_str = target_date.strftime("%Y-%m-%d")
        
        url = f"{self.base_url}?date={date_str}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                papers = response.json()
                
                logger.info(
                    "Collected %d papers from Hugging Face for date: %s",
                    len(papers),
                    date_str,
                )
                
                for paper in papers:
                    # Extract fields
                    paper_id = paper.get("paper", {}).get("id")
                    title = paper.get("paper", {}).get("title")
                    summary = paper.get("paper", {}).get("summary", "")
                    
                    # Construct URL
                    paper_url = f"https://huggingface.co/papers/{paper_id}"
                    
                    if not paper_id or not title:
                        continue
                        
                    # Create RawItem
                    item = RawItem(
                        source_platform="huggingface",
                        source_id=paper_id,
                        original_title=title,
                        original_text=summary,
                        title_cn="", # Will be filled by LLM
                        url=paper_url,
                        published_at=datetime.combine(target_date, datetime.min.time()),
                        category="学术论文", # Default category for papers
                        heat_score=hf_config.get("base_heat", 80.0) # High default heat for daily papers
                    )
                    items.append(item)

        except Exception as e:
            logger.error("Error collecting from Hugging Face: %s", e)

        logger.info(f"Hugging Face collection complete. Total items: {len(items)}")
        return items
