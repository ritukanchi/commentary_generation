#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventLogicService:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'frame-descriptions',
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='event_logic_service',
            auto_offset_reset='earliest'

        )
        
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
    def detect_emotion(self, description):
        # predefined set of emotions that we defined then compressed from the new.ipynb under detection_service since 
        # that list was too exhaustive, tried to make a temporary bracket if the milvus did not work 
        emotions = {
            'excitement': ['goal', 'celebrating', 'cheering', 'spectacular', 'amazing', 'incredible'],
            'tension': ['save', 'block', 'defense', 'pressure', 'intense', 'crucial'],
            'joy': ['victory', 'win', 'success', 'happy', 'celebration', 'triumph'],
            'disappointment': ['miss', 'failed', 'lost', 'mistake', 'error', 'unfortunate'],
            'surprise': ['unexpected', 'sudden', 'shocking', 'surprising'],
            'neutral': ['running', 'positioning', 'tactical', 'movement', 'passing']
        }
        
        description_lower = description.lower()
        
        for emotion, keywords in emotions.items():
            if any(keyword in description_lower for keyword in keywords):
                return emotion
                
        return 'neutral'
        
    def calculate_confidence(self, description, emotion):
        return 0.85  # placeholder 

    def process_descriptions(self):
        logger.info("Event Logic Service started")
        
        for message in self.consumer:
            try:
                description_data = message.value
                description = description_data['description']
                
                emotion = self.detect_emotion(description)
                confidence = self.calculate_confidence(description, emotion)
                
                emotion_message = {
                    'video_path': description_data['video_path'],
                    'frame_number': description_data['frame_number'],
                    'timestamp': description_data['timestamp'],
                    'description': description,
                    'detected_emotion': emotion,
                    'emotion_confidence': confidence,
                    'processed_at': datetime.now().isoformat()
                }
                
                self.producer.send('emotion-events', emotion_message)
                logger.info(f"Detected Emotion '{emotion}' for Frame {description_data['frame_number']}")
                
            except Exception as e:
                logger.error(f"Error processing emotion: {e}")

if __name__ == "__main__":
    service = EventLogicService()
    service.process_descriptions()
