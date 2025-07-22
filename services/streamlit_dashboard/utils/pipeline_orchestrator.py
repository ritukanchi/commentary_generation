# services/pipeline_orchestrator/main.py
import os
import json
import time
from kafka import KafkaConsumer, KafkaProducer
from utils.videoprocessor import process_video_pipeline

class PipelineOrchestrator:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
    def start_pipeline(self, video_path, video_name, fps=1):
        """Start the sequential pipeline"""
        print(f"Starting pipeline for {video_name}")
        
        # Step 1: Frame Ingestion
        self.trigger_frame_ingestion(video_path, video_name, fps)
        
        # Step 2: Wait for frames to be processed and trigger detection
        self.monitor_and_trigger_next_service('video-frames', 'detection-service')
        
        # Continue for other services...
        
    def trigger_frame_ingestion(self, video_path, video_name, fps):
        """Trigger frame ingestion service"""
        message = {
            'action': 'start_processing',
            'video_path': video_path,
            'video_name': video_name,
            'fps': fps
        }
        self.producer.send('pipeline-control', message)
        
    def monitor_and_trigger_next_service(self, topic_to_monitor, next_service):
        """Monitor a topic and trigger next service when ready"""
        pass
