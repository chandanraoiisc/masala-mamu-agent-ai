import openai
from io import BytesIO
import os

import base64

from dotenv import load_dotenv
# Load the .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure your .env file has this

def predict_gpt4o(image):
    # Convert PIL image to bytes
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    buffered.seek(0)

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a grocery bill reader. Extract only the vegetable or fruit names and their quantities and prices from the image with a space separating each line.Output should be in the below format with no additional text: Drumstick 5kg Rs.5 Lady Finger 5kg Rs.60 Zucchini 250g Rs.60 Pineapple 1kg Rs.5 Mango 1kg Rs.60 Passion Fruit 2 Rs.60 Watermelon 1kg Rs.20 Mushroom 2kg Rs.20 Litchi 5 Rs.50 Raw Banana 3 Rs.50"},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buffered.read()).decode()}},
                ]
            }
        ],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()
