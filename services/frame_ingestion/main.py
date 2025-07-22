import cv2
import os
import json
import base64
import time
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer  
import uuid

producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:9092,kafka2:9092,kafka3:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# dummy logic not implemented 
"""
consumer = KafkaConsumer(
    'video-processing-requests',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:9092,kafka2:9092,kafka3:9092'),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='frame-ingestion-service',
    auto_offset_reset='latest'
)"""

def extract_frames(video_path, fps=1, video_name=None):

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Failed to open video: {video_path}")
        return False

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps == 0:
        print("Unable to get FPS from video.")
        return False

    if video_name is None:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # new uuid for this video processing ensures dynamic shiz
    session_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    frame_dir = f"{video_name}_{timestamp}_{session_id}"
    output_dir = f"/app/dataset/frames/{frame_dir}"
    os.makedirs(output_dir, exist_ok=True)

    interval = int(video_fps / fps)
    count = 0
    frame_index = 0

    print(f"Starting frame extraction for {video_name}")
    print(f"Output directory: {output_dir}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % interval == 0:
            frame_filename = f"frame_{count:06d}.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            cv2.imwrite(frame_path, frame)

            # conversion of frame to base64 for kafka purposes
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')

            frame_message = {
                'video_path': video_path,
                'video_name': video_name,
                'frame_number': count,
                'frame_index': frame_index,
                'timestamp': datetime.now().isoformat(),
                'frame_data': frame_b64,
                'saved_path': frame_path,
                'session_id': session_id,
                'frame_directory': frame_dir
            }

            producer.send('video-frames', frame_message)
            print(f"Sent frame {count} from {video_name} - Saved to: {frame_path}")
            frame_index += 1

        count += 1

    cap.release()
    producer.flush()
    print(f"Extracted and sent {frame_index} frames from: {video_name}")
    print(f"Frames saved to: {output_dir}")
    return True

def process_uploaded_video(video_path, video_name, fps=1):
    # elegant try catch cause first time failed miserably
    try:
        clean_name = os.path.splitext(video_name)[0]
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        success = extract_frames(video_path, fps, clean_name)
        return success
    except Exception as e:
        print(f"Error processing uploaded video: {e}")
        return False

def listen_for_processing_requests():
    # consuming requests from streamlit seski(not) dashboard
    consumer = KafkaConsumer(
        'video-processing-requests',
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='frame-ingestion-service',
        auto_offset_reset='earliest'
    )
    
    print(" Frame Ingestion Service listening for requests...")
    print(f" Kafka servers: {os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')}")
    
    for message in consumer:
        request = message.value
        if request['action'] == 'process_video':
            print(f"Received processing request for: {request['video_name']}")
            success = process_uploaded_video(
                request['video_path'], 
                request['video_name'], 
                request['fps']
            )
            if success:
                print(f"Successfully processed {request['video_name']}")
            else:
                print(f"Failed to process {request['video_name']}")
                return False 

if __name__ == "__main__":
    listen_for_processing_requests()
