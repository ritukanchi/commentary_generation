#!/usr/bin/env python3
# another test file 
import os
import json
import logging
import time
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from TTS.api import TTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'commentary-text',
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='tts_service'
        )

        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        self.audio_output_dir = '/audio-output'
        os.makedirs(self.audio_output_dir, exist_ok=True)

        self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

    def generate_tts_audio(self, text, emotion):
        try:
            timestamp = int(time.time())
            filename = f"commentary_{timestamp}_{emotion}.wav"
            file_path = os.path.join(self.audio_output_dir, filename)

            self.tts.tts_to_file(text=text, file_path=file_path)
            logger.info(f"Generated TTS audio: {file_path}")

            return file_path
        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return None

    def process_commentary(self):
        logger.info("TTS service started...")

        for message in self.consumer:
            try:
                data = message.value
                commentary = data['commentary']
                emotion = data['emotion']

                audio_path = self.generate_tts_audio(commentary, emotion)

                if audio_path:
                    audio_metadata = {
                        'video_path': data['video_path'],
                        'frame_number': data['frame_number'],
                        'timestamp': data['timestamp'],
                        'commentary': commentary,
                        'emotion': emotion,
                        'audio_file': audio_path,
                        'processed_at': datetime.now().isoformat()
                    }

                    self.producer.send('audio-output', audio_metadata)
                    logger.info(f"Published audio metadata for frame {data['frame_number']}")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

if __name__ == "__main__":
    service = TTSService()
    service.process_commentary()
