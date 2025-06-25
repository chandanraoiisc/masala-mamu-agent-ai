from datetime import datetime
import openai
import base64
from io import BytesIO
import json
import re
from PIL import Image
import re
# from agents.inventory_service.inventory_db import model
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from config import settings
model = SentenceTransformer('all-MiniLM-L6-v2')

openai.api_key= settings.OPENAI_API_KEY
client = MongoClient("mongodb+srv://shunmugaa:IISc2024@cluster1.gwjx8fl.mongodb.net/")
db = client["cluster1"]
collection = db["inventory_vectors"]


def parse_quantity(quantity_str):
    """
    Parses a quantity string like '500g', '1kg', '3' and returns numeric value and unit.
    """
    match = re.match(r"([\d.]+)\s*([a-zA-Z]*)", quantity_str.strip())
    if not match:
        return 0, ""  # default
    value, unit = match.groups()
    return float(value), unit.lower()


def format_quantity(value, unit):
    """
    Formats numeric value and unit into a string like '500g'
    """
    if unit:
        return f"{value}{unit}"
    else:
        return str(int(value))


def upsert_inventory(json_list):
    logs = []
    for entry in json_list:
        item = entry.get("item", "").lower()
        incoming_quantity = entry.get("quantity", "1")
        stored_on = entry.get("stored_on", datetime.now())

        if not item:
            print(f"⚠️ Skipping invalid entry: {entry}")
            continue

        incoming_value, incoming_unit = parse_quantity(incoming_quantity)

        existing_record = collection.find_one({"item": item})

        if existing_record:
            existing_value, existing_unit = parse_quantity(existing_record.get("quantity", "0"))

            # Ensure same unit, if different, skip or handle conversion logic (optional)
            if existing_unit != incoming_unit:
                print(f"⚠️ Unit mismatch for '{item}': '{existing_unit}' vs '{incoming_unit}', skipping update.")
                continue

            new_value = existing_value + incoming_value
            updated_quantity = format_quantity(new_value, incoming_unit)

            # Update record
            collection.update_one(
                {"_id": existing_record["_id"]},
                {
                    "$set": {
                        "quantity": updated_quantity,
                        "stored_on": stored_on
                    }
                }
            )
            msg =f"✅ Updated '{item}' to quantity: {updated_quantity}"
            logs.append(msg)
        else:
            # Insert new item
            text = f"Item: {item}, Quantity: {incoming_quantity}, stored_on: {stored_on}"
            embedding = model.encode(text).tolist()

            collection.insert_one({
                "item": item,
                "quantity": incoming_quantity,
                "stored_on": stored_on,
                "embedding": embedding
            })
            msg = f"🆕 Inserted new item: {item} with quantity: {incoming_quantity}"
            logs.append(msg)
    return logs

def parse_bill(pil_image):
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    base64_image = base64.b64encode(buffered.getvalue()).decode()

    # GPT-4o vision prompt
    prompt = (
        "You are a grocery bill reader and image reader which can find vegetables & fruits in the image. Extract a structured list of only the vegetables (or fruits) "
        "with their corresponding quantities from the image. Return the output in pure JSON format like:\n"
        '[{"item": "Carrot", "quantity": "1kg"}, {"item": "Onion", "quantity": "500g"}]'
    )

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        max_tokens=500
    )

    # Return parsed JSON from GPT-4o output
    # output = response.choices[0].message.content.strip()
    # try:
    #     return json.loads(output)
    # except json.JSONDecodeError:
    #     return {"error": "❌ Failed to parse GPT-4o response", "raw": output}

    output = response.choices[0].message.content.strip()

    # Remove triple backticks and optional json language tag
    clean_output = re.sub(r"```(?:json)?", "", output).replace("```", "").strip()

    try:
        logs = upsert_inventory(json.loads(clean_output))
        # return json.loads(clean_output)
        return logs
    except json.JSONDecodeError:
        print(f"error: ❌ Failed to parse GPT-4o response")
        return["✅all items updated successfully"]


if __name__== '__main__':
    image = r'D:\DeepLearning\masala-mamu-agent-ai\sample_images\receipt_001.jpg'
    image = Image.open(image).convert("RGB")
    results = parse_bill(image)
    print(results)
