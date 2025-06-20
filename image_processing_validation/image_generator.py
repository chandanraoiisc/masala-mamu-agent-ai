
from icrawler.builtin import BingImageCrawler

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


# Combine into master list
master_list = vegetables + fruits

# Download images for each item
for item in master_list:
    print(f"Downloading images for: {item}")
    crawler = BingImageCrawler(storage={'root_dir': f'vegetable_dataset/{item}'})
    crawler.crawl(keyword=f'{item} vegetable', max_num=100)
