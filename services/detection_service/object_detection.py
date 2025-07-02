from ultralytics import YOLO
import cv2
import os
import json
import zipfile

FRAME_DIR = "/Datasets/frames"
OUTPUT_DIR = "Datasets/Object_detection_frames_with_metadata"
OUTPUT_ZIP = "Object_detection_frames_metadata.zip"

os.makedirs(OUTPUT_DIR, exist_ok=True)

model = YOLO("yolov8m.pt")

frame_files = sorted([
    f for f in os.listdir(FRAME_DIR)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
])

print(f"Found {len(frame_files)} frames.")

for frame_file in frame_files:
    img_path = os.path.join(FRAME_DIR, frame_file)
    img = cv2.imread(img_path)

    if img is None:
        print(f" Could not read {img_path}")
        continue

    results = model.predict(img, conf=0.3)

    boxes = []
    detections_json = []

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        if cls_id in [0, 32]:  # 0=person, 32=sports ball
            boxes.append(box)

            # Save detection metadata
            detections_json.append({
                "class": results[0].names[cls_id],
                "confidence": float(box.conf[0]),
                "bbox": [float(x) for x in box.xyxy[0]]
            })

    # Draw boxes manually (smaller labels)
    annotated = img.copy()
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls_id = int(box.cls[0])
        label = results[0].names[cls_id]
        conf = box.conf[0]

        # Box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Label
        text = f"{label} {conf:.2f}"
        cv2.putText(
            annotated,
            text,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA
        )

    # Save annotated image
    out_name = f"obj_det_{os.path.splitext(frame_file)[0]}.jpg"
    out_path = os.path.join(OUTPUT_DIR, out_name)
    cv2.imwrite(out_path, annotated)

    json_name = f"obj_det_{os.path.splitext(frame_file)[0]}.json"
    json_path = os.path.join(OUTPUT_DIR, json_name)
    with open(json_path, "w") as f:
        json.dump({
            "frame": frame_file,
            "detections": detections_json
        }, f, indent=2)

print("Detection and metadata saving complete!")

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, start=folder_path)
                zipf.write(abs_path, rel_path)
    print(f" Zipped '{folder_path}' into '{output_path}'")

zip_folder(OUTPUT_DIR, OUTPUT_ZIP)
