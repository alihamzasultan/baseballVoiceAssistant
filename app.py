import os
import base64
from flask import Flask, render_template, request, jsonify
import openai
from dotenv import load_dotenv
import json

with open('2024rules.json', 'r', encoding='utf-8') as file:
    faq_data = json.load(file)

with open('Misunderstood.json', 'r', encoding='utf-8') as file:
    misunderstood = json.load(file)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=api_key)

# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Load Images data
import json


def load_faq_data():
    with open('baseball_rules2024.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Ensure data is a list of dictionaries with "page" and "content" keys
    if isinstance(data, list) and all(isinstance(item, dict) and "page" in item and "content" in item for item in data):
        return data  # Return the structured list directly

    raise ValueError("Unexpected JSON structure. Expected a list of dictionaries with 'page' and 'content' keys.")


from rapidfuzz import process, fuzz

def find_top_matches(user_input, data):
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("Data should be a list of dictionaries.")

    # Normalize pages to lowercase strings and store a reference dictionary
    choices = {str(item.get("page", "")).lower(): item for item in data if "page" in item}

    # Ensure the user input is also normalized
    user_input = str(user_input).lower()

    # Use fuzzy matching to get the top 100 best matches
    matches = process.extract(user_input, choices.keys(), scorer=fuzz.QRatio, limit=10)

    # Return the corresponding items from data
    sorted_matches = [choices[match[0]] for match in matches]

    return sorted_matches  # Returns top 100 matches


conversation_history = []
@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_input = request.form.get("user_input", "").strip().lower()

    try:
                # Load image data and find top matches
        image_data = load_faq_data()
        sorted_matches = find_top_matches(user_input, image_data)[:100]  # Get only the top 10 matches
        # print(json.dumps(sorted_matches, indent=2, ensure_ascii=False))

        # Create the custom prompt with matched results
        custom_prompt = f"""
        You are an AI assistant for an baseball rules, you will tell users about baseball rules.
        Here is all the infermation, rules and regulations.

        please add a backslash n where line ends. 

        BAY AREA MEN’S SENIOR BASEBALL LEAGUE
        Rules & Regulations: 
        {json.dumps(faq_data, indent=2, ensure_ascii=False)}


        Baseball Rules 2024:
        {json.dumps(sorted_matches, indent=2, ensure_ascii=False)}

        Misunderstood rules:
        {json.dumps(misunderstood, indent=2, ensure_ascii=False)}


        """
        conversation_text = "\n".join([f"User: {entry['user']}\nAI: {entry['ai']}" for entry in conversation_history])
        full_prompt = f"{custom_prompt}\n{conversation_text}\nUser: {user_input}\nAI:"

        # Handle other chatbot input
        
        prompt_with_custom = f"{full_prompt}\n{user_input}"
        completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_with_custom}]
        )
        gpt_response = completion.choices[0].message.content
        conversation_history.append({"user": user_input, "ai": gpt_response})
        return jsonify({"response": gpt_response})
        
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
