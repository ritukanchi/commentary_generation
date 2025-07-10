import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ✅ Read from .env
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

# 1. Connect to Milvus
connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
print(f"✅ Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")

# 2. Load CSV
df = pd.read_csv("data/emotions_train.csv")
captions = df["caption"].astype(str).tolist()
emotions = df["emotion"].astype(str).tolist()

# 3. Generate embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(captions, convert_to_numpy=True)

# 4. Define schema
collection_name = "caption_emotions"

if collection_name in Collection.list():
    collection = Collection(name=collection_name)
    collection.drop()

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
    FieldSchema(name="emotion", dtype=DataType.VARCHAR, max_length=32)
]
schema = CollectionSchema(fields, description="Football captions + emotion vectors")

# 5. Create collection
collection = Collection(name=collection_name, schema=schema)
collection.create_index(field_name="embedding", index_params={
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}
})
collection.load()
print("✅ Collection created and indexed.")

# 6. Insert data
entities = [
    embeddings.tolist(),  # embeddings must be first if no ID
    emotions
]
collection.insert(entities)
collection.flush()
print(f"✅ Inserted {len(captions)} caption embeddings into '{collection_name}'")

# 7. Test search (optional)
collection.load()
results = collection.search(
    data=[embeddings[0]],
    anns_field="embedding",
    param={"metric_type": "L2", "params": {"nprobe": 10}},
    limit=3,
    output_fields=["emotion"]
)

print("\n🔍 Sample search results:")
for result in results[0]:
    print(f"Emotion: {result.entity.get('emotion')}, Score: {result.distance:.4f}")
