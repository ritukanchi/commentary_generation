# emotion_classifier.py

import re
import json
from typing import Tuple, List

def classify_emotion_from_description(text: str) -> Tuple[str, float]:
    """
    Rule-based emotion classifier based on keywords from image description.
    Returns a tuple of (emotion_label, confidence_score).
    """
    text = text.lower()

    if re.search(r"\bgoal\b", text):
        return "excitement", 0.95
    elif re.search(r"shot\b.*\bnear goal", text) or "attempt on goal" in text:
        return "anticipation", 0.85
    elif "passing sequence" in text or "pass" in text:
        return "calm", 0.75
    elif "defensive action" in text or "blocked shot" in text:
        return "nervousness", 0.8
    elif "players arguing" in text or "foul" in text:
        return "anger", 0.9
    elif "celebration" in text:
        return "joy", 0.9
    elif "goalkeeper saves" in text:
        return "relief", 0.8
    elif "missed opportunity" in text or "near miss" in text:
        return "disappointment", 0.7
    else:
        return "neutral", 0.6


if __name__ == "__main__":
    input_txt = "../dataset/image_descriptions.txt"
    output_json = "../dataset/emotions_by_frame.json"

    results = []
    try:
        with open(input_txt, "r") as f:
            lines = f.read().split("\n")

        current_frame = {}
        for line in lines:
            if line.startswith("[Frame"):
                if current_frame:
                    results.append(current_frame)
                current_frame = {"frame": line.strip()}
            elif line.startswith("URL: "):
                current_frame["url"] = line.replace("URL: ", "").strip()
            elif line.startswith("Description:"):
                current_frame["description"] = ""
            elif line.strip() == "":
                continue
            else:
                if "description" in current_frame:
                    current_frame["description"] += line.strip() + " "

        if current_frame:
            results.append(current_frame)

        # Classify emotions
        for item in results:
            desc = item.get("description", "")
            emotion, confidence = classify_emotion_from_description(desc)
            item["predicted_emotion"] = emotion
            item["confidence"] = round(confidence, 2)

        with open(output_json, "w") as out:
            json.dump(results, out, indent=2)

        print(f"Emotion predictions saved to {output_json}")

    except Exception as e:
        print(f"Failed to process file: {e}")
