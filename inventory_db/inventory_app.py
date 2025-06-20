import streamlit as st
from inventory_db import upsert_inventory
from PIL import Image
import torch
import easyocr
import numpy as np
from rag import generate_answer
import openai
import base64
from io import BytesIO
import json
from gpt_image_reader import predict_vegetables_gpt4o

# def load_models():
#     clip_model = CLIPModel.from_pretrained("laion/CLIP-ViT-B-32-laion2B-s34B-b79K")
#     clip_processor = CLIPProcessor.from_pretrained("laion/CLIP-ViT-B-32-laion2B-s34B-b79K")
#     ocr_reader = easyocr.Reader(['en'])  # Load English reader
#     return clip_processor, clip_model, ocr_reader

# clip_processor, clip_model, ocr_reader = load_models()


vegetables = [
    "Potato", "Onion", "Tomato", "Carrot", "Cabbage", "Cauliflower", "Brinjal",
    "Beans", "Peas", "Drumstick", "Pumpkin", "Radish", "Turnip", "Beetroot",
    "Capsicum", "Bell Pepper", "Spinach", "Amaranth", "Coriander", "Mint", "Curry Leaves",
    "Bottle Gourd", "Bitter Gourd", "Ridge Gourd", "Snake Gourd", "Ash Gourd",
    "Cucumber", "Zucchini", "Broccoli", "Mushroom", "Green Chilli", "Red Chilli",
    "Sweet Potato", "Yam", "Raw Banana", "Spring Onion", "Leek", "Fenugreek Leaves",
    "Lettuce", "Okra", "Lady Finger", "Celery", "Avocado", "Corn", "Garlic", "Ginger"
]
fruits = [
    "Apple", "Banana", "Mango", "Papaya", "Pineapple", "Grapes", "Orange", "Mosambi",
    "Watermelon", "Muskmelon", "Guava", "Pomegranate", "Kiwi", "Strawberry",
    "Blueberry", "Raspberry", "Chikoo", "Custard Apple", "Litchi", "Pear",
    "Peach", "Plum", "Apricot", "Dates", "Fig", "Coconut", "Jackfruit", "Avocado",
    "Dragon Fruit", "Passion Fruit", "Tangerine", "Cherry", "Blackberry"
]

labels = vegetables + fruits


detected_veggies = set()

st.title("Smart Grocery Image Classifier + Assistant")



# ---- User Input Row (Text + Image + Audio) ----
st.markdown("### 💬 Ask or Add Inventory")

user_text = st.text_input("Type your query", placeholder="E.g., Add 2 kg tomatoes, What’s in inventory?", label_visibility="collapsed")

image_button = st.file_uploader("➕", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

# Process text query via RAG
if user_text:
    st.info("🧠 Answering with RAG...")
    response = generate_answer(user_text)
    st.write(response)

if image_button:
    image = Image.open(image_button).convert("RGB")
    st.image(image, caption="Uploaded Image", use_container_width=True)

    st.write("🧠 Extracting with GPT-4o...")
    gpt_results = predict_vegetables_gpt4o(image)

    if isinstance(gpt_results, list):
        st.success("✅ Extracted Grocery Items:")
        for item in gpt_results:
            st.markdown(f"- 🥬 **{item['item']}** — 🧮 Quantity: `{item['quantity']}`")

        # You can store or process this list as needed
        detected_veggies = {item["item"] for item in gpt_results}

    else:
        st.error(gpt_results.get("error", "Failed to read response"))
        st.markdown("**🔍 GPT-4o Raw Output:**")
        st.code(gpt_results.get("raw", ""), language="json")
    st.markdown("---")
    st.subheader("📝 Review and Edit Detected Items")

    # Header row for editable table
    header_cols = st.columns([3, 2, 1])
    with header_cols[0]:
        st.markdown("**Item Name**")
    with header_cols[1]:
        st.markdown("**Quantity**")
    with header_cols[2]:
        st.markdown("**Include**")

    # Initialize
    final_list = []
    include_all = st.checkbox("Include All", value=True)

    # Ensure detected_veggies is a list of dicts from GPT-4o
    if isinstance(gpt_results, list) and all("item" in x and "quantity" in x for x in gpt_results):
        with st.form("edit_form"):
            for i, entry in enumerate(gpt_results):
                cols = st.columns([3, 2, 1])
                with cols[0]:
                    edited_item = st.text_input("Item", key=f"item_{i}", value=entry["item"].title(), label_visibility="collapsed")
                with cols[1]:
                    quantity = st.text_input("Qty", key=f"qty_{i}", value=entry["quantity"], label_visibility="collapsed")
                with cols[2]:
                    include = st.checkbox("", value=include_all, key=f"include_{i}")

                if include and edited_item.strip():
                    final_list.append({
                        "item": edited_item.strip(),
                        "quantity": quantity.strip()
                    })

            submitted = st.form_submit_button("Save Final List")

        if submitted:
            st.success("🎉 Final grocery list ready!")
            st.json(final_list)


            upsert_inventory(final_list)
            st.subheader("🥬🥬🥬Current Inventory Items")
            st.write(generate_answer('Fetch all '))

