import os
import shutil
import json
import time
from datetime import datetime

def process_video_pipeline(video_path, video_name, fps, shared_dir="/app/services/shared"):
    try:
        os.makedirs(shared_dir, exist_ok=True)
        shared_video_path = os.path.join(shared_dir, f"uploaded_{int(time.time())}_{video_name}")
        shutil.copy2(video_path, shared_video_path)
        request_data = {
            'video_path': shared_video_path,
            'video_name': video_name,
            'fps': fps,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        with open(os.path.join(shared_dir, f"request_{int(time.time())}.json"), 'w') as f:
            json.dump(request_data, f)
        return True
    except Exception as e:
        print(f"Video processing error: {e}")
        return False
