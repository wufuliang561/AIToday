from fastapi import FastAPI
from app.core.config import settings
from app.api.endpoints import feed, hotspots
from app.db.session import engine
from app.db.base import Base
from app.models.item import RawItem
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.collectors.base import BaseCollector
from app.services.collectors.rss import RSSCollector
from app.services.collectors.youtube import YouTubeCollector
from app.services.collectors.huggingface import HuggingFaceCollector
from app.services.processor import Processor
from app.services.clustering import ClusteringService
from app.db.session import SessionLocal
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo
from typing import List
from datetime import datetime
import asyncio
import logging

from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

try:
    scheduler_timezone = ZoneInfo(settings.TIMEZONE)
except Exception:
    logger.warning("Invalid timezone '%s', falling back to UTC", settings.TIMEZONE)
    scheduler_timezone = ZoneInfo("UTC")

# Create tables
# 创建数据库表
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning("Could not create tables on startup: %s", e)

scheduler = AsyncIOScheduler(timezone=scheduler_timezone)

async def execute_collector_pipeline(run_label: str, collectors: List[BaseCollector]):
    logger.info("[%s] Starting pipeline with %d collectors", run_label, len(collectors))
    db = SessionLocal()
    try:
        processor = Processor()
        clustering = ClusteringService(db)

        all_items = []
        for collector in collectors:
            try:
                logger.info("[%s] Collector %s started", run_label, collector.__class__.__name__)
                items = await collector.collect()
                logger.info("[%s] Collector %s finished, pulled %d items", run_label, collector.__class__.__name__, len(items))
                all_items.extend(items)
            except Exception:
                logger.exception("[%s] Error in collector %s", run_label, collector.__class__.__name__)

        if not all_items:
            logger.info("[%s] No items collected; skipping persistence and clustering", run_label)
            return

        saved_items = 0
        for item in all_items:
            existing = db.query(RawItem).filter(RawItem.source_id == item.source_id).first()
            if existing:
                logger.info(
                    "[%s] Skipping duplicate (source_id=%s, title=%s)",
                    run_label,
                    item.source_id,
                    item.title_cn or item.original_title,
                )
                continue

            try:
                processed_item = await processor.process_item(item)
                if not processed_item:
                    logger.info(
                        "[%s] Discarded non-AI item (source_id=%s)",
                        run_label,
                        item.source_id,
                    )
                    continue

                db.add(processed_item)
                db.commit()
                saved_items += 1
                logger.info(
                    "[%s] Saved item #%s from %s: %s",
                    run_label,
                    processed_item.id,
                    processed_item.source_platform,
                    processed_item.title_cn or processed_item.original_title,
                )
            except IntegrityError:
                db.rollback()
                logger.info(
                    "[%s] Skipping duplicate on commit (source_id=%s)",
                    run_label,
                    item.source_id,
                )
            except Exception:
                db.rollback()
                logger.exception("[%s] Error saving item (source_id=%s)", run_label, item.source_id)

        if saved_items:
            await clustering.cluster_items()
            logger.info("[%s] Pipeline complete, saved %d new items.", run_label, saved_items)
        else:
            logger.info("[%s] No new items saved; skipping clustering", run_label)
        
    finally:
        db.close()

async def run_rss_task():
    await execute_collector_pipeline("RSS Task", [RSSCollector()])

async def run_youtube_task():
    await execute_collector_pipeline("YouTube Task", [YouTubeCollector()])

async def run_huggingface_task():
    await execute_collector_pipeline("Hugging Face Task", [HuggingFaceCollector()])

@asynccontextmanager
async def lifespan(app: FastAPI):
    first_run_at = datetime.now(tz=scheduler_timezone)  # fire once immediately after startup
    # 启动调度器
    scheduler.add_job(
        run_rss_task,
        'interval',
        hours=2,
        id="rss_collection",
        replace_existing=True,
        next_run_time=first_run_at,
    )
    scheduler.add_job(
        run_youtube_task,
        'cron',
        hour="8,20",
        minute=0,
        id="youtube_collection",
        replace_existing=True,
        next_run_time=first_run_at,
    )
    scheduler.add_job(
        run_huggingface_task,
        'cron',
        hour="9", # Daily papers usually updated by then
        minute=0,
        id="huggingface_collection",
        replace_existing=True,
        next_run_time=first_run_at,
    )
    scheduler.start()
    logger.info(
        (
            "Scheduler started (timezone=%s). RSS every 2h, "
            "YouTube daily at 08:00/20:00, Hugging Face daily at 09:00. "
            "First run executes immediately on startup."
        ),
        scheduler_timezone,
    )
    
    yield
    
    # 关闭调度器
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 跨域资源共享 (CORS) 配置
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feed.router, prefix=f"{settings.API_V1_STR}/feed", tags=["feed"])
app.include_router(hotspots.router, prefix=f"{settings.API_V1_STR}/hotspots", tags=["hotspots"])

@app.get("/")
def root():
    return {"message": "Welcome to AIToday Backend"}
