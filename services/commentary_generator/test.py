#!/usr/bin/env python3
# not important dummy test file 
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OUTPUT_DIR = os.getenv("TTS_OUTPUT_DIR", "./tts_test_outputs")

def generate_commentary(description, emotion, context=""):

    url = "https://api.mistral.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    EVENT <{description}>
    TONE <{emotion}>
    CONTEXT {context}

    TASK Write two sentences . Make it human-like and expressive.
    """

    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "temperature": 0.7
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        print(f"Error: Mistral API returned status {response.status_code}")
        return f"Simple fallback commentary. Description: {description}"

def save_commentary_json(input_data, commentary):
 
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"commentary_frame_test.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    output_data = {
        "frame": input_data.get("frame"),
        "url": input_data.get("url"),
        "description": input_data.get("description"),
        "emotion": input_data.get("predicted_emotion"),
        "commentary": commentary,
        "processed_at": datetime.now().isoformat()
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Saved commentary JSON to {filepath}")

def main():
    input_file = "../../Datasets/event_comm_gen.json"

    with open(input_file, "r", encoding="utf-8") as f:
        input_data = json.load(f)[0]  

    description = input_data["description"]
    emotion = input_data["predicted_emotion"]

    context = "- Example 1\n- Example 2\n- Example 3"

    commentary = generate_commentary(description, emotion, context)

    save_commentary_json(input_data, commentary)

if __name__ == "__main__":
    main()
