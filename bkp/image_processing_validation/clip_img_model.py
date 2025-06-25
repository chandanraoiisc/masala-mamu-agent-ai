from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
import os

# Load CLIP
clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

# Classes
classes = os.listdir("vegetable_dataset")

# Prediction loop
def predict_clip(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = clip_processor(text=classes, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = clip_model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)
    pred = classes[torch.argmax(probs).item()]
    return pred
