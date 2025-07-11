#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommentaryGeneratorService:
    def __init__(self):  # kafka consumer and producer DO NOT TOUCH
        self.consumer = KafkaConsumer(
            'emotion-events',
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='commentary_generator_service'
        )
        
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        self.mistral_api_key = os.getenv('MISTRAL_API_KEY')
        
        # Initialize Milvus connection
        self.setup_milvus()  
        
        # Create output directory if needed
        self.output_dir = os.getenv("TTS_OUTPUT_DIR", "./tts_outputs")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def setup_milvus(self):
        """Setup Milvus vector database connection"""
        try:
            from pymilvus import connections, Collection
            
            connections.connect(
                host=os.getenv('MILVUS_HOST', 'localhost'),
                port=int(os.getenv('MILVUS_PORT', '19530'))
            )
            
            self.collection = Collection('commentary_embeddings')
            logger.info("Connected to Milvus")
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            self.collection = None
    
    def get_contextual_commentary(self, description, emotion):
        """Get contextual commentary from Milvus"""
        if not self.collection:
            return []
        try:
            # Placeholder
            return []
        except Exception as e:
            logger.error(f"Error getting contextual commentary: {e}")
            return []
    
    def generate_commentary_with_mistral(self, description, emotion, context):
        """Generate commentary using Mistral API"""
        try:
            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.mistral_api_key}',
                'Content-Type': 'application/json'
            }
            prompt = f"""
            EVENT <{description}>
            TONE <{emotion}>
            CONTEXT {context}
            TASK Write two sentences. Make it human-like and expressive.
            """
            payload = {
                'model': 'mistral-small-latest',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 100,
                'temperature': 0.7
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"Mistral API error: {response.status_code}")
                return self.generate_fallback_commentary(description, emotion)
        except Exception as e:
            logger.error(f"Error calling Mistral API: {e}")
            return self.generate_fallback_commentary(description, emotion)
    
    def generate_fallback_commentary(self, description, emotion):
        """Generate fallback commentary when API fails"""
        emotion_intros = {
            'excitement': "What an incredible moment! ",
            'tension': "The pressure is building here... ",
            'joy': "Absolutely brilliant! ",
            'disappointment': "Oh no, that's unfortunate... ",
            'neutral': "And here we see... "
        }
        return emotion_intros.get(emotion, "") + description
        
    def save_commentary_json(self, data, frame_number):
        """
        Save commentary data to a JSON file
        """
        filename = f"com_gen_frame_{frame_number:03d}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved commentary JSON to {filepath}")

    def process_emotions(self):
        """Process emotions and generate commentary"""
        logger.info("Commentary generation service started")
        
        for message in self.consumer:
            try:
                emotion_data = message.value
                description = emotion_data['description']
                emotion = emotion_data['detected_emotion']

                context = self.get_contextual_commentary(description, emotion)
                commentary = self.generate_commentary_with_mistral(description, emotion, context)

                commentary_message = {
                    'video_path': emotion_data['video_path'],
                    'frame_number': emotion_data['frame_number'],
                    'timestamp': emotion_data['timestamp'],
                    'description': description,
                    'emotion': emotion,
                    'commentary': commentary,
                    'processed_at': datetime.now().isoformat()
                }

                # Send to Kafka
                self.producer.send('commentary-text', commentary_message)
                logger.info(f"Generated commentary for frame {emotion_data['frame_number']}")

                # Save to JSON file
                self.save_commentary_json(commentary_message, emotion_data['frame_number'])

            except Exception as e:
                logger.error(f"Error generating commentary: {e}")

if __name__ == "__main__":
    service = CommentaryGeneratorService()
    service.process_emotions()
