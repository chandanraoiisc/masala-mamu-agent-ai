import openai
import base64
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Set OpenAI API key from .env
openai.api_key = os.getenv("OPENAI_API_KEY")

def predict_gpt4o(image_path):
    # Read and encode the image
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # Make a call to OpenAI's GPT-4o model with image + text input
    response = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What vegetables are in this image? Return only the names in this list ['Potato', 'Cabbage', 'Beans', 'Tomato', 'Carrot']."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=100
    )

    return response.choices[0].message.content

# print(predict_gpt4o('veg_sample/Beans/000001.jpg',['Beans','Peas','Tomato']))
