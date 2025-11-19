from app.db.session import SessionLocal
from app.models.item import RawItem

db = SessionLocal()
items = db.query(RawItem).all()
print(f"Total items: {len(items)}")
categorized = [i for i in items if i.category]
print(f"Categorized items: {len(categorized)}")
if categorized:
    print(f"Sample category: {categorized[0].category}")
else:
    print("No items have categories.")
db.close()
