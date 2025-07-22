import os
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections, Collection, FieldSchema, CollectionSchema, 
    DataType, utility, exceptions
)
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommentaryVectorDB:
    def __init__(self, host: str = "localhost", port: int = 19530, 
                 collection_name: str = "commentary_embeddings"):
        """
        Initialize the Commentary Vector Database
        
        Args:
            host: Milvus server host
            port: Milvus server port  
            collection_name: Name of the collection to use
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        self.is_connected = False
        
    def connect(self) -> bool:
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                timeout=30
            )
            self.is_connected = True
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
    
    def _create_schema(self) -> CollectionSchema:
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="commentary_text", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="emotion", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="context", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
            FieldSchema(name="timestamp", dtype=DataType.INT64)
        ]
        
        return CollectionSchema(
            fields=fields,
            description="Commentary embeddings with emotional and contextual data",
            enable_dynamic_field=True
        )
    
    def setup_collection(self) -> bool:
        """Set up collection with proper indexing"""
        if not self.is_connected:
            logger.error("Not connected to Milvus")
            return False
            
        try:
            if utility.has_collection(self.collection_name):
                logger.info(f"Dropping existing collection: {self.collection_name}")
                utility.drop_collection(self.collection_name)
            
            schema = self._create_schema()
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
                using='default',
                shards_num=2
            )
            
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params,
                timeout=30
            )
            
            self.collection.load()
            
            logger.info(f"Collection '{self.collection_name}' created and loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup collection: {e}")
            return False
    
    def load_data_from_csv(self, csv_path: str, 
                          text_column: str = "commentary_text",
                          emotion_column: str = "emotion",
                          context_column: str = "context") -> bool:
        """Load data from CSV file with flexible column mapping"""
        try:
            if not os.path.exists(csv_path):
                logger.error(f"CSV file not found: {csv_path}")
                return False
                
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            texts = df[text_column].fillna("").astype(str).tolist()
            emotions = df[emotion_column].fillna("neutral").astype(str).tolist()
            contexts = df[context_column].fillna("") if context_column in df.columns else [""] * len(texts)
            contexts = pd.Series(contexts).astype(str).tolist()
            
            logger.info("Generating embeddings...")
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            timestamps = [int(pd.Timestamp.now().timestamp())] * len(texts)
            
            # Insert data
            entities = [
                embeddings.tolist(),
                texts,
                emotions,
                contexts,
                timestamps
            ]
            
            insert_result = self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"Successfully inserted {len(texts)} records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data from CSV: {e}")
            return False
    
    def search_similar_commentary(self, query_text: str, 
                                emotion_filter: Optional[str] = None,
                                top_k: int = 3) -> List[Dict[str, Any]]:
        try:
            query_embedding = self.model.encode([query_text])
            
            # build search expression
            expr = f"emotion == '{emotion_filter}'" if emotion_filter else None
            
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            # perform search
            results = self.collection.search(
                data=query_embedding,
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["commentary_text", "emotion", "context"]
            )
            
            # format results
            formatted_results = []
            for result in results[0]:
                formatted_results.append({
                    "commentary_text": result.entity.get("commentary_text"),
                    "emotion": result.entity.get("emotion"),
                    "context": result.entity.get("context"),
                    "distance": result.distance,
                    "similarity_score": 1 / (1 + result.distance) 
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_contextual_commentary(self, scene_description: str, 
                                detected_emotion: str, 
                                top_k: int = 3) -> List[Dict[str, Any]]:
        results = self.search_similar_commentary(
            query_text=scene_description,
            emotion_filter=detected_emotion,
            top_k=top_k
        )
        
        if not results:
            results = self.search_similar_commentary(
                query_text=scene_description,
                top_k=top_k
            )
        
        return results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            stats = {
                "total_entities": self.collection.num_entities,
                "collection_name": self.collection_name,
                "is_loaded": utility.load_state(self.collection_name).state,
                "schema": str(self.collection.schema)
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

def main():
    load_dotenv()
    
    # Initialize database
    db = CommentaryVectorDB(
        host="localhost",  
        port=19530,
        collection_name="commentary_embeddings"
    )
    
    if not db.connect():
        logger.error("Failed to connect to Milvus")
        return False
    
    if not db.setup_collection():
        logger.error("Failed to setup collection")
        return False
    
    csv_path = "commentary_embeddings.csv"
    if os.path.exists(csv_path):
        if not db.load_data_from_csv(
            csv_path=csv_path,
            text_column="caption",  
            emotion_column="emotion",
            context_column="confidence"  
        ):
            logger.error("Failed to load data from CSV")
            return False
    
    test_query = "exciting football match with crowd cheering"
    test_emotion = "excitement"
    
    results = db.get_contextual_commentary(test_query, test_emotion)
    
    logger.info(f"Search results for '{test_query}' with emotion '{test_emotion}':")
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. Text: {result['commentary_text'][:100]}...")
        logger.info(f"   Emotion: {result['emotion']}")
        logger.info(f"   Similarity: {result['similarity_score']:.4f}")
    
    stats = db.get_collection_stats()
    logger.info(f"Collection stats: {stats}")
    
    return True

if __name__ == "__main__":
    main()
