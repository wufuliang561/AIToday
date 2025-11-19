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
# Create tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables on startup: {e}")

scheduler = AsyncIOScheduler()

async def run_collection_task():
    print("Starting collection task...")
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

        # Save and Process Items
        for item in all_items:
            # Check if exists
            # (In a real app, we'd query DB first or use ON CONFLICT DO NOTHING)
            # Here we just try to add and ignore if fails (or rely on unique constraint)
            try:
                # Process (Translate/Summarize)
                processed_item = await processor.process_item(item)
                db.add(processed_item)
                db.commit()
            except Exception as e:
                db.rollback()
                # print(f"Error saving item: {e}") # Duplicate likely

        # Run Clustering
        await clustering.cluster_items()
        print("Collection and processing complete.")
        
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler
    scheduler.add_job(run_collection_task, 'interval', hours=2)
    scheduler.start()
    
    # Run once on startup for demo purposes
    asyncio.create_task(run_collection_task())
    
    yield
    
    # Shutdown scheduler
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
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
