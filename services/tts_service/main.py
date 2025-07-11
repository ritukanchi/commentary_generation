#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer

# Import TTS
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

        # Load the TTS model
        self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

        # Make sure output dir exists
        os.makedirs("audio_output", exist_ok=True)
        
    def generate_tts_with_coqui(self, text, emotion):
        """Generate TTS using Coqui TTS"""
        try:
            timestamp = int(datetime.now().timestamp())
            audio_file = f"audio_output/commentary_{timestamp}_{emotion}.wav"

            # Actually generate speech
            self.tts.tts_to_file(
                text=text,
                file_path=audio_file
            )

            logger.info(f"Generated TTS audio: {audio_file}")
            return audio_file

        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return None
        
    def process_commentary(self):
        """Process commentary and generate TTS"""
        logger.info("TTS service started")
        
        for message in self.consumer:
            try:
                commentary_data = message.value
                commentary_text = commentary_data['commentary']
                emotion = commentary_data['emotion']

                # Generate TTS
                audio_file = self.generate_tts_with_coqui(commentary_text, emotion)

                if audio_file:
                    audio_message = {
                        'video_path': commentary_data['video_path'],
                        'frame_number': commentary_data['frame_number'],
                        'timestamp': commentary_data['timestamp'],
                        'commentary': commentary_text,
                        'emotion': emotion,
                        'audio_file': audio_file,
                        'processed_at': datetime.now().isoformat()
                    }

                    self.producer.send('audio-output', audio_message)
                    logger.info(f"Generated TTS for frame {commentary_data['frame_number']}")

            except Exception as e:
                logger.error(f"Error processing TTS: {e}")

if __name__ == "__main__":
    service = TTSService()
    service.process_commentary()
