from fastapi import FastAPI
from app.core.config import settings
from app.api.endpoints import feed, hotspots
from app.db.session import engine
from app.db.base import Base
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.collectors.rss import RSSCollector
from app.services.collectors.youtube import YouTubeCollector
from app.services.collectors.twitter import TwitterCollector
from app.services.collectors.reddit import RedditCollector
from app.services.processor import Processor
from app.services.clustering import ClusteringService
from app.db.session import SessionLocal
from contextlib import asynccontextmanager
import asyncio

# Create tables
# 创建数据库表
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables on startup: {e}")

scheduler = AsyncIOScheduler()

async def run_collection_task():
    print("Starting collection task... (开始采集任务...)")
    db = SessionLocal()
    try:
        collectors = [
            RSSCollector(),
            YouTubeCollector(),
            # TwitterCollector(),
            # RedditCollector()
        ]
        
        processor = Processor()
        clustering = ClusteringService(db)
        
        all_items = []
        for collector in collectors:
            try:
                items = await collector.collect()
                all_items.extend(items)
            except Exception as e:
                print(f"Error in collector {collector.__class__.__name__}: {e}")

        # 保存并处理条目
        for item in all_items:
            # 优化：在处理前检查是否存在，以节省 LLM 成本
            existing = db.query(RawItem).filter(RawItem.source_id == item.source_id).first()
            if existing:
                # print(f"Skipping duplicate: {item.title_cn or item.original_title}")
                continue

            try:
                # 处理（翻译/总结）
                processed_item = await processor.process_item(item)
                db.add(processed_item)
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Error saving item: {e}")

        # 运行聚类
        await clustering.cluster_items()
        print("Collection and processing complete. (采集和处理完成。)")
        
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动调度器
    scheduler.add_job(run_collection_task, 'interval', hours=2)
    scheduler.start()
    
    # 启动时运行一次（用于演示）
    asyncio.create_task(run_collection_task())
    
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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feed.router, prefix=f"{settings.API_V1_STR}/feed", tags=["feed"])
app.include_router(hotspots.router, prefix=f"{settings.API_V1_STR}/hotspots", tags=["hotspots"])

@app.get("/")
def root():
    return {"message": "Welcome to AIToday Backend"}
