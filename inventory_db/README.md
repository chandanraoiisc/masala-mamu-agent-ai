 # Overview
This project implements an intelligent Inventory Management Agent to manage grocery stock by leveraging:

- MongoDB for storing inventory data

- Vector search with RAG (Retrieval-Augmented Generation) for contextual understanding

- Prompt engineering for natural language-based DB operations

- Object detection + OCR for automated updates via image inputs (vegetables and bills)


# System Features
## 🔍 1. Context-Aware Querying with RAG
Uses Retrieval-Augmented Generation with GPT-4o to answer user queries.
Inventory stored in MongoDB with fields:

- itemnm (Item Name)
- quantity
- stored_on (Timestamp)
- embedding (Vector for semantic similarity)

The ItemNm field is embedded using Sentence Transformer MiniLLM in a 386 dim vector space.
A vector index is created on embedding for enabling semantic search using RAG.
GPT-4o parses user intent (Insert / Update / Delete / Fetch) from natural language using prompt engineering.

## ✍️ 2. Prompt-based CRUD Operations
User input is parsed to determine:

Action type: Insert, Update, Delete, Fetch
Target item(s) and fields
Actions are then executed on the MongoDB collection:

- Insert: Adds a new grocery item with quantity and timestamp
- Update: Changes quantity or metadata
- Delete: Removes item from inventory
- Fetch: Retrieves available stock information

## 📷 3. Image Input & Interpretation

### 🔍 a. Object Detection on Vegetable Images
Users can upload images of vegetables.

GPT-4o performs object detection to identify vegetable types.

User receives a confirmation form (Human In Loop) to verify detected data before updating the inventory.

### 🧾 b. OCR on Grocery Bills
Supports image upload of handwritten or printed bills.

GPT-4o extracts:
- Item names
- Corresponding quantities

A human-in-the-loop form validates extracted entries before database update.

### 📊 c. Human Confirmation
All automated detections go through a user confirmation step.

Ensures correctness and prevents accidental updates.

## ⚙️ 4. Model Evaluation
Multiple models were tested for:
Object detection & OCR

GPT-4o outperformed other models in:

- Multi-language OCR (including handwritten Tamil/English mix).
- It has low WER & CER in OCR detection & high accuracy in object detection.
- Accuracy in low-light or occluded vegetable images
- Speed of processing.


## 🚀 Future Improvements

- Integrate barcode scanning from grocery packages.

- Enable voice commands for accessibility.
