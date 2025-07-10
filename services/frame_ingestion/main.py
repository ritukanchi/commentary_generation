import cv2
import os
import json
import base64
import time
from datetime import datetime
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def extract_frames(video_path, fps=1):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f" Failed to open video: {video_path}")
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps == 0:
        print("Unable to get FPS from video.")
        return

    interval = int(video_fps / fps)
    count = 0
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % interval == 0:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')

            frame_message = {
                'video_path': video_path,
                'frame_number': count,
                'timestamp': datetime.now().isoformat(),
                'frame_data': frame_b64
            }

            producer.send('video-frames', frame_message)
            print(f"Sent frame {count} from {video_path}")
            frame_index += 1

        count += 1

    cap.release()
    producer.flush()
    print(f"Extracted and sent {frame_index} frames from: {video_path}")

def batch_process_videos(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_path = os.path.join(root, file)
                extract_frames(video_path)

if __name__ == "__main__":
    input_dir = "services/dataset/videos/soccernet_videos/england_epl"
    batch_process_videos(input_dir)
