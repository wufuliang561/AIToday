from app.db.session import SessionLocal
from app.models.item import RawItem
from app.models.hotspot import Hotspot # 修复 FK 错误

db = SessionLocal()
item = db.query(RawItem).first()
if item:
    print(f"Updating item: {item.title_cn or item.original_title}")
    item.category = "行业新闻"
    db.commit()
    print("Item updated with category '行业新闻'")
else:
    print("No items found.")
db.close()
