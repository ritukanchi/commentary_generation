import os
import requests
import json
import time
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime
from kafka import KafkaProducer

# Load credentials
load_dotenv("../../.env")

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
TURBOLINE_API_KEY = os.getenv("TURBOLINE_API_KEY")
TURBOLINE_API_URL = os.getenv("TURBOLINE_API_URL")
CLOUDINARY_UPLOAD_URL = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload"

# Kafka setup
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = "frame-descriptions"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)


def analyze_existing_frames(input_dir):
    results = []
    frame_index = 0

    image_files = sorted([
        f for f in os.listdir(input_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    total_frames = len(image_files)
    start_time = time.time()

    for file_name in tqdm(image_files, desc="Processing frames", unit="frame"):
        img_path = os.path.join(input_dir, file_name)

        try:
            with open(img_path, "rb") as img_file:
                upload_resp = requests.post(
                    CLOUDINARY_UPLOAD_URL,
                    files={"file": img_file},
                    data={"upload_preset": "ml_default"}
                )

            if upload_resp.status_code == 200:
                response_json = upload_resp.json()
                img_url = response_json.get("secure_url")

                if img_url:
                    prompt = (
                        "You are a computer vision expert analyzing a soccer match frame. Provide a detailed description of the image. "
                        "Include: total number of visible players, jersey numbers if visible, team assignment based on jersey color, "
                        "ball location (if visible), proximity to goal, and any visible actions (e.g. shot, pass, defense). Be descriptive but structured."
                    )

                    payload = {
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": img_url}}
                                ]
                            }
                        ],
                        "max_tokens": 500
                    }

                    headers = {
                        "Content-Type": "application/json",
                        "tl-key": TURBOLINE_API_KEY
                    }

                    turbo_resp = requests.post(TURBOLINE_API_URL, headers=headers, json=payload)

                    if turbo_resp.status_code == 200:
                        try:
                            content = turbo_resp.json()["choices"][0]["message"]["content"]

                            detection_output = {
                                "video_path": img_path,
                                "frame_number": frame_index,
                                "timestamp": datetime.now().isoformat(),
                                "description": content,
                                "processed_at": datetime.now().isoformat()
                            }

                            # Send to Kafka
                            producer.send(KAFKA_TOPIC, detection_output)

                            results.append(detection_output)

                        except Exception as parse_error:
                            print(f"Failed to parse TurboLine response for {file_name}: {parse_error}")
                    else:
                        print(f"TurboLine API error for frame {file_name}: {turbo_resp.text}")
                else:
                    print(f"Cloudinary upload failed for {file_name}: No secure_url in response.")
            else:
                print(f"Cloudinary upload failed for {file_name} (Status {upload_resp.status_code}): {upload_resp.text}")

        except FileNotFoundError:
            print(f"File not found: {img_path}")
        except Exception as e:
            print(f"Unexpected error with {file_name}: {e}")

        frame_index += 1

    producer.flush()
    end_time = time.time()
    elapsed = end_time - start_time
    fps = total_frames / elapsed if elapsed > 0 else 0

    print(f"\nCompleted {total_frames} frames in {elapsed:.2f} seconds ({fps:.2f} FPS)")
    return results


def save_descriptions(descriptions, output_txt_path):
    try:
        with open(output_txt_path, "w") as f:
            for item in descriptions:
                f.write(json.dumps(item, indent=2))
                f.write("\n\n")
        print(f"All frame descriptions saved to: {output_txt_path}")
    except Exception as e:
        print(f"Failed to write descriptions to file: {e}")


if __name__ == "__main__":
    input_dir = "../dataset/frames/frametest"
    output_txt = "../dataset/image_descriptions.txt"

    descriptions = analyze_existing_frames(input_dir)
    save_descriptions(descriptions, output_txt)
