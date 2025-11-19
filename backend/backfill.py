import asyncio
from app.db.session import SessionLocal
from app.models.item import RawItem
from app.models.hotspot import Hotspot # 修复 FK 错误
from app.services.processor import Processor

async def backfill():
    db = SessionLocal()
    items = db.query(RawItem).filter(RawItem.category == None).limit(3).all() # 限制为 3 个
    print(f"Found {len(items)} items to backfill.")
    
    processor = Processor()
    
    for item in items:
        print(f"Processing: {item.id} - {item.original_title[:30]}...")
        try:
            # 我们需要重置 title_cn 以触发翻译（如果我们想要重新翻译）
            # 但是 process_item 使用 original_title，所以它会覆盖 title_cn
            await processor.process_item(item)
            db.add(item)
            db.commit()
            print(f"  -> Category: {item.category}")
            await asyncio.sleep(2) # 避免速率限制
        except Exception as e:
            print(f"  -> Error: {e}")
            db.rollback()
            
    db.close()

if __name__ == "__main__":
    asyncio.run(backfill())
