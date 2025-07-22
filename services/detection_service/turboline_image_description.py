# another test file for the turboline api testing

import os
import base64
import requests
import json
from dotenv import load_dotenv

load_dotenv("../../.env")

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
TURBOLINE_API_KEY = os.getenv("TURBOLINE_API_KEY")
TURBOLINE_API_URL = os.getenv("TURBOLINE_API_URL")

def analyze_existing_frames(input_dir):
    results = []
    frame_index = 0

    image_files = sorted([
        f for f in os.listdir(input_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    for file_name in image_files:
        img_path = os.path.join(input_dir, file_name)

        with open(img_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode("utf-8")

        # ImgBB testing till website went out of whack so :(
        upload_resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": encoded}
        )

        if upload_resp.status_code == 200:
            img_url = upload_resp.json()["data"]["url"]
            print(f" Uploaded: {file_name} -> {img_url}")

            # request to turboline
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "You are an advanced vision analysis model. For the following soccer image, extract structured data as JSON. "
                                    "Include the following keys: 'object_tags' (list of all detected objects and their bounding boxes), "
                                    "'ball_trajectory_vector' (x,y motion vector of the ball if visible), and 'event_likelihood_scores' "
                                    "(dictionary of event names like 'goal', 'shot', 'pass' with likelihood percentages). Respond ONLY in JSON format without extra commentary."
                                )
                            },
                            {"type": "image_url", "image_url": {"url": img_url}}
                        ]
                    }
                ],
                "max_tokens": 400
            }

            headers = {
                "Content-Type": "application/json",
                "tl-key": TURBOLINE_API_KEY
            }

            turbo_resp = requests.post(TURBOLINE_API_URL, headers=headers, json=payload)

            if turbo_resp.status_code == 200:
                description = turbo_resp.json()["choices"][0]["message"]["content"]
                print(f"Frame {frame_index} Description received.")
                results.append({
                    "frame_index": frame_index,
                    "filename": file_name,
                    "image_url": img_url,
                    "description": description
                })
            else:
                print(f"Turboline API error: {turbo_resp.text}")

        else:
            print(f" ImgBB upload error: {upload_resp.text}")

        frame_index += 1

    return results

def save_descriptions(descriptions, output_txt_path):
    with open(output_txt_path, "w") as f:
        for item in descriptions:
            f.write(f"[Frame {item['frame_index']}] {item['filename']}\n")
            f.write(f"URL: {item['image_url']}\n")
            f.write(f"Description:\n{item['description']}\n\n")
    print(f"All frame descriptions saved to: {output_txt_path}")

if __name__ == "__main__":
    input_dir = "../../Datasets/all_frames_output"  
    output_txt = "../../Datasets/all_frames_desc.txt"

    descriptions = analyze_existing_frames(input_dir)
    save_descriptions(descriptions, output_txt)
