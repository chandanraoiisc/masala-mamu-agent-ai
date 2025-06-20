import os
import random
from PIL import Image, ImageDraw, ImageFont
from faker import Faker
from tqdm import tqdm
import numpy as np

fake = Faker()
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

items = vegetables + fruits

quantities = ["250g", "500g", "1kg", "2kg", "5kg", "1", "2", "3", "5"]
prices = [5, 10, 20, 30, 40, 50, 60]

# Setup
output_dir = "synthetic_bills"
font_dir = "fonts"
os.makedirs(output_dir, exist_ok=True)

# Load fonts
font_files = ["PatrickHand-Regular.ttf", "DancingScript-Regular.ttf", "HomemadeApple-Regular.ttf"]
fonts = []
for fname in font_files:
    fpath = os.path.join(font_dir, fname)
    try:
        fonts.append(ImageFont.truetype(fpath, 20))
    except:
        pass

if not fonts:
    fonts = [ImageFont.load_default()]

def add_gaussian_noise(img, mean=0, std=20):
    """Adds Gaussian noise to an image"""
    np_img = np.array(img).astype(np.float32)
    noise = np.random.normal(mean, std, np_img.shape)
    noisy_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_img)

for i in tqdm(range(1, 301), desc="Generating noisy bills"):
    img = Image.new("RGB", (400, 600), color="white")
    draw = ImageDraw.Draw(img)

    store = fake.company()
    date = fake.date()
    y = 20

    # Header
    draw.text((random.randint(10, 30), y), store, font=random.choice(fonts), fill="black")
    y += random.randint(25, 35)
    draw.text((random.randint(10, 30), y), f"Date: {date}", font=random.choice(fonts), fill="black")
    y += random.randint(35, 45)

    num_items = random.randint(5, 10)
    selected_items = random.sample(items, num_items)
    lines = []

    for item in selected_items:
        qty = random.choice(quantities)
        price = random.choice(prices)
        line = f"{item} {qty} Rs.{price}"
        x_jitter = random.randint(10, 40)
        draw.text((x_jitter, y), line, font=random.choice(fonts), fill="black")
        lines.append(line)
        y += random.randint(28, 35)  # Vertical jitter

    total = sum([int(l.split("Rs.")[-1]) for l in lines])
    y += random.randint(15, 25)
    draw.text((random.randint(10, 30), y), f"Total: Rs.{total}", font=random.choice(fonts), fill="black")

    # Add Gaussian noise
    noisy_img = add_gaussian_noise(img)

    # Save
    img_path = os.path.join(output_dir, f"receipt_{i:03d}.jpg")
    text_path = os.path.join(output_dir, f"receipt_{i:03d}.txt")
    noisy_img.save(img_path)
    with open(text_path, "w") as f:
        f.write("\n".join(lines))