
import re
import json
from agents.inventory_service.llm_agent import prompt,llm
from agents.inventory_service.inventory_db import upsert_inventory,collection,get_vectorstore
from langchain_core.runnables.base import Runnable
import time

def generate_answer(query_text: str):
    # Fetch relevant docs for RAG
    # docs = retriever.get_relevant_documents(query_text)
    vectorstore = get_vectorstore()  # you already defined this in db.py
    # retriever = vectorstore.as_retriever()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 100})
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
    # print("rag answer",type(answer),answer)
    if 'intent' in answer.lower():
        try:
            parsed = json.loads(answer)

        # Normalize to list if it's a single dictionary
            if isinstance(parsed, dict):
                parsed_list = [parsed]
            elif isinstance(parsed, list):
                parsed_list = parsed
            else:
                raise ValueError("Parsed JSON is not a dict or list.")
        except json.JSONDecodeError as e:
            print("❌ Failed to parse JSON:", e)
        
        print("✅ Parsed list:", parsed_list)

        for action in parsed_list:
                print(action)
                intent = action.get("Intent", "").lower()
                data = action.get("Data", {})
        
                if intent == "insert":
                    print(type(data))
                    upsert_inventory([data])
                    print(f"✅ Inserted {data['item']}.")
                elif intent == "update":
                # Similar to insert but only update quantity if item exists
                    result = collection.update_one(
                        {"item": data["item"].lower()},
                        {"$set": {"quantity": data["quantity"]}}
                    )
                    if result.matched_count == 0:
                        print(f"⚠️ Update failed, item not found: {data}")
                    else:
                        print(f"🔁 Updated: {data['item']}")

                elif intent == "delete":
                    result = collection.delete_many({
                        "item": data["item"].lower()
                    })
                    if result.deleted_count == 0:
                        print(f"⚠️ Delete failed, item not found: {data}")
                    else:
                        print(f"❌ Deleted: {data['item']}")

                else:
                    print(f"⚠️ Unknown intent: {intent}")
            

        # Otherwise, assume it's a general query
    return answer


