import json
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from torch.nn.functional import softmax
from tqdm import tqdm
import os

# --- CONFIG ---
input_json_path = "data/captions_extracted/captions/train.caption_coco_format.json"
output_csv_path = "data/emotions_train.csv"

# --- Load model ---
model_name = "joeddav/distilbert-base-uncased-go-emotions-student"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
model.eval()

# --- Load captions from JSON ---
with open(input_json_path, "r") as f:
    data = json.load(f)

captions = [ann["caption"] for ann in data["annotations"]]

# --- Predict emotions ---
results = []
batch_size = 16

for i in tqdm(range(0, len(captions), batch_size), desc="Processing Captions"):
    batch = captions[i:i+batch_size]
    inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = softmax(outputs.logits, dim=1)

    top_indices = torch.argmax(probs, dim=1)
    top_confidences = torch.max(probs, dim=1).values

    for caption, idx, conf in zip(batch, top_indices, top_confidences):
        results.append({
            "caption": caption,
            "emotion": model.config.id2label[int(idx)],
            "confidence": round(conf.item(), 4)
        })

# --- Save to CSV ---
df = pd.DataFrame(results)
os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
df.to_csv(output_csv_path, index=False)
print(f" Saved emotion CSV to: {output_csv_path}")

