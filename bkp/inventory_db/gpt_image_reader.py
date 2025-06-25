import openai
import base64
from io import BytesIO
import json
import re
from PIL import Image

openai.api_key='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'
def predict_vegetables_gpt4o(pil_image):
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
        return json.loads(clean_output)
    except json.JSONDecodeError:
        return {"error": "❌ Failed to parse GPT-4o response", "raw": output}


if __name__== '__main__':
    image = r'D:\DeepLearning\masala-mamu-agent-ai\sample_images\receipt_001.jpg'
    image = Image.open(image).convert("RGB")
    results = predict_vegetables_gpt4o(image)
    print(results)
