import os
import requests
import json
import base64
import io
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv

load_dotenv("../../.env")

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
TURBOLINE_API_KEY = os.getenv("TURBOLINE_API_KEY")
TURBOLINE_API_URL = os.getenv("TURBOLINE_API_URL")
CLOUDINARY_UPLOAD_URL = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload"

#kafka set up consumer -> producer 
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka1:9092,kafka2:9092,kafka3:9092")

consumer = KafkaConsumer(
    'video-frames',
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='detection-service',
    auto_offset_reset='earliest'
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def analyze_frame_from_kafka(frame_data):
    """Analyze frame received from Kafka topic"""
    try:
        print(f"🧪 Processing frame {frame_data['frame_number']} from {frame_data['video_name']}")

        # decode base64 image of kafka 
        frame_b64 = frame_data['frame_data']
        frame_bytes = base64.b64decode(frame_b64)

        # Upload to Cloudinary (third party URL hosting for turboline functionality processing)
        upload_resp = requests.post(
            CLOUDINARY_UPLOAD_URL,
            files={"file": io.BytesIO(frame_bytes)},
            data={"upload_preset": "ml_default"}
        )

        if upload_resp.status_code == 200:
            response_json = upload_resp.json()
            img_url = response_json.get("secure_url")

            if img_url:
                prompt = ( # specific prompt to the turboline API 
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
                    content = turbo_resp.json()["choices"][0]["message"]["content"]

                    detection_output = {
                        "video_path": frame_data['video_path'],
                        "video_name": frame_data['video_name'],
                        "frame_number": frame_data['frame_number'],
                        "frame_index": frame_data.get('frame_index', frame_data['frame_number']),
                        "timestamp": frame_data['timestamp'],
                        "description": content,
                        "processed_at": datetime.now().isoformat(),
                        "session_id": frame_data['session_id'],
                        "frame_directory": frame_data['frame_directory']
                    }

                    # send result to Kafka
                    producer.send('frame-descriptions', detection_output)
                    print(f"Sent frame {frame_data['frame_number']} analysis to frame-descriptions topic")
                    return detection_output
                else:
                    print(f"TurboLine API error: {turbo_resp.text}")
            else:
                print(" Cloudinary upload failed: No secure_url returned")
        else:
            print(f" Cloudinary upload failed: {upload_resp.status_code} - {upload_resp.text}")

    except Exception as e:
        print(f" Error analyzing frame: {e}")
        return None

def start_detection_service():
    #consume frames and analysing 
    print(" Starting Detection Service...")
    print(f"Listening on topic: video-processing-requests")
    print(f" Kafka servers: {KAFKA_BOOTSTRAP_SERVERS}")

    try:
        for message in consumer:
            frame_data = message.value
            print(f"Received frame {frame_data['frame_number']} from {frame_data['video_name']}")
            analyze_frame_from_kafka(frame_data)
    except Exception as e:
        print(f"Kafka consumer error: {e}")
    finally:
        consumer.close()
        producer.close()

if __name__ == "__main__":
    start_detection_service()
