import json
import os
import google.generativeai as genai
from collections import defaultdict

# File paths
products_file = "products.json"
categories_file = "categories.json"

# --------------------------
# Initialize Gemini
# --------------------------
GEMINI_API_KEY="AIzaSyDeehLxqPNCBNKe3kZ-HQe2z4WM4S7R8qc"
genai.configure(api_key=GEMINI_API_KEY)

# Gemini helper
# --------------------------
def get_completion_from_messages(messages, model="gemini-1.5-flash", temperature=0.3):
    """
    Convert role-based messages into a single prompt and query Gemini.
    """
    # Flatten role-based messages into one text prompt
    prompt = ""
    for m in messages:
        role = m["role"].upper()
        prompt += f"{role}: {m['content']}\n\n"

    chat = genai.GenerativeModel(model)
    response = chat.generate_content(prompt)
    return response.text.strip()

# --------------------------
# Categories + Products
# --------------------------
def get_categories():
    with open(categories_file, "r") as f:
        return json.load(f)

def get_products():
    with open(products_file, "r") as f:
        return json.load(f)

def get_products_by_category(category):
    products = get_products()
    return [p for p in products.values() if p["category"] == category]

def get_product_by_name(name):
    products = get_products()
    return products.get(name, None)

# --------------------------
# Extract entities
# --------------------------
def find_category_and_product(user_input, products_and_category):
    """
    Use Gemini to extract categories and product names mentioned in the user input.
    Returns a JSON-like string.
    """
    delimiter = "####"
    system_message = f"""
    You will be provided with customer service queries. 
    The query will be inside {delimiter}.
    
    Output a Python list of JSON objects with this format:
        'category': <one of {list(products_and_category.keys())}>,
    OR
        'products': <a list of products that appear in the query>.
    
    If nothing matches, return [].
    Products must match from the allowed list below:
    {products_and_category}
    """
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{user_input}{delimiter}"}
    ]
    return get_completion_from_messages(messages)

def read_string_to_list(input_string):
    """
    Convert Gemini's string output into a Python list of dicts.
    """
    if not input_string:
        return []
    try:
        input_string = input_string.replace("'", '"')  # normalize quotes
        return json.loads(input_string)
    except json.JSONDecodeError:
        print("Error parsing JSON:", input_string)
        return []

# --------------------------
# Lookup details
# --------------------------
def generate_output_string(data_list):
    """
    Take extracted entities and return product info as a string.
    """
    output_string = ""
    for data in data_list:
        if "products" in data:
            for product_name in data["products"]:
                product = get_product_by_name(product_name)
                if product:
                    output_string += json.dumps(product, indent=4) + "\n"
        elif "category" in data:
            category = data["category"]
            for product in get_products_by_category(category):
                output_string += json.dumps(product, indent=4) + "\n"
    return output_string

# --------------------------
# Generate chatbot reply
# --------------------------
def answer_user_msg(user_msg, product_info):
    delimiter = "####"
    system_message = """
    You are a customer service assistant for an online grocery store. 
    Respond in a friendly and helpful tone, with concise answers. 
    Make sure to ask relevant follow-up questions.
    """
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{user_msg}{delimiter}"},
        {"role": "assistant", "content": f"Relevant product information:\n{product_info}"}
    ]
    return get_completion_from_messages(messages)
