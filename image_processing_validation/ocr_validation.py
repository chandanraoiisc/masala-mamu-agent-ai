import re

def normalize_line(line):
    # Remove dashes, colons, extra spaces
    line = re.sub(r'[-•]', '', line)           # remove bullets/dashes
    line = re.sub(r':', '', line)              # remove colons
    line = re.sub(r'\s+', ' ', line).strip()   # normalize whitespace
    line = line.replace("Rs.", "Rs").replace("Rs ", "Rs")  # standardize Rs
    return line

def extract_items(text):
    items = []
    for line in text.strip().splitlines():
        norm = normalize_line(line)
        match = re.match(r'(.+?)\s+([\d\.]+[a-zA-Z]*)\s+Rs(\d+)', norm)
        if match:
            name, quantity, price = match.groups()
            items.append({
                "name": name.strip().lower(),
                "quantity": quantity.strip().lower(),
                "price": price.strip()
            })
    return items

def compare_texts(expected_text, actual_text):
    expected_items = extract_items(expected_text)
    actual_items = extract_items(actual_text)

    matched = []
    missed = []
    extra = []

    actual_copy = actual_items.copy()
    for exp in expected_items:
        if exp in actual_copy:
            matched.append(exp)
            actual_copy.remove(exp)
        else:
            missed.append(exp)
    
    extra = actual_copy

    return {
        "matched": matched,
        "missed": missed,
        "extra": extra,
        "accuracy": len(matched) / len(expected_items) if expected_items else 0
    }
