# agents/inventory_service/inventory_store.py
from pymongo import MongoClient

client = MongoClient("mongodb+srv://shunmugaa:IISc2024@cluster1.gwjx8fl.mongodb.net/")
db = client["cluster1"]
collection = db["inventory_vectors"]

def fetch_all_inventory():
    try:
        records = collection.find()
        return [
            {
                "name": doc.get("item"),
                "quantity": doc.get("quantity"),
                "unit": "unknown",  # optionally map if unit exists
                # "stored_on": doc.get("stored_on").strftime("%Y-%m-%d") if doc.get("stored_on") else None
            }
            for doc in records
        ]
    except Exception as e:
        print(f"❌ Error fetching inventory: {e}")
        return []

print(fetch_all_inventory())