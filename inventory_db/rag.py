
import re
import json
from llm_agent import retriever,prompt,llm
from inventory_db import upsert_inventory,collection
from langchain_core.runnables.base import Runnable
import time

def generate_answer(query_text: str):
    # Fetch relevant docs for RAG
    # docs = retriever.get_relevant_documents(query_text)
    docs = retriever.get_relevant_documents(query_text, search_kwargs={"k": 100})

    context = "\n".join(doc.page_content for doc in docs)

    # Call LLM with structured prompt
    chain = prompt | llm


    try:
        # Your usual logic
        response = chain.invoke({"query_text": query_text,"context":context})
         
    except Exception as e:
        print("❌ Error in Groq API:", str(e))
        return "⚠️ Failed to get response from the AI model. Please try again shortly."

  
    # Parse response
    answer = response.content
    print(answer)
    try:
        parsed_list = json.loads(answer)
        print("✅ Parsed list:", parsed_list)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON:", e)
    # Handle JSON actions
    print(len(parsed_list))
    for action in parsed_list:
            print(action)
            intent = action.get("Intent", "").lower()
            data = action.get("Data", {})
    
            if intent == "insert":
                print(type(data))
                upsert_inventory([data])
                return f"✅ Inserted {data['item']}."
            elif intent == "update":
            # Similar to insert but only update quantity if item exists
                result = collection.update_one(
                    {"item": data.get("item"), "stored_on": data.get("stored_on")},
                    {"$set": {"quantity": data.get("quantity")}}
                )
                if result.matched_count == 0:
                    print(f"⚠️ Update failed, item not found: {data}")
                else:
                    print(f"🔁 Updated: {data['item']}")

            elif intent == "delete":
                result = collection.delete_one({
                    "item": data.get("item"),
                    "stored_on": data.get("stored_on")
                })
                if result.deleted_count == 0:
                    print(f"⚠️ Delete failed, item not found: {data}")
                else:
                    print(f"❌ Deleted: {data['item']}")

            else:
                print(f"⚠️ Unknown intent: {intent}")
        

    # Otherwise, assume it's a general query
    return answer


