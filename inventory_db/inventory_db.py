from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

from langchain.embeddings import HuggingFaceEmbeddings
# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# MongoDB setup
client = MongoClient("mongodb+srv://shunmugaa:IISc2024@cluster1.gwjx8fl.mongodb.net/")
db = client["cluster1"]
collection = db["inventory_vectors"]


embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_vectorstore():
    from pymongo import MongoClient
    from langchain_community.vectorstores.mongodb_atlas import MongoDBAtlasVectorSearch


    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="inv_search" , # Replace with your index name
        text_key="item"
    )
    return vectorstore
def upsert_inventory(json_list):
    for entry in json_list:
        

        item = entry.get("item")
        quantity = entry.get("quantity", "1")
        stored_on = entry.get("stored_on")

        # Validate required fields
        if not item or not stored_on:
            print(f"⚠️ Skipping entry with missing 'item' or 'stored_on': {entry}")
            continue

        # Generate embedding
        text = f"Item: {item}, Quantity: {quantity}, stored_on: {stored_on}"
        embedding = model.encode(text).tolist()

        # Upsert to MongoDB using item + stored_on as composite key
        collection.update_one(
            {"item": item, "stored_on": stored_on},
            {
                "$set": {
                    "item": item,
                    "quantity": quantity,
                    "stored_on": stored_on,
                    "embedding": embedding
                }
            },
            upsert=True
        )
