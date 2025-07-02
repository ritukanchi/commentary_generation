import cv2
import os

def extract_frames(video_path, output_dir, fps=1):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps == 0:
        print("❌ Unable to get FPS from video.")
        return

    interval = int(video_fps / fps)
    count = 0
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % interval == 0:
            frame_file = os.path.join(output_dir, f"frame_{frame_index:05}.jpg")
            cv2.imwrite(frame_file, frame)
            frame_index += 1

        count += 1

    cap.release()
    print(f"✅ Extracted {frame_index} frames from: {video_path}")

def batch_process_videos(root_dir, output_root):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".mkv"):
                video_path = os.path.join(root, file)
                # Create a unique output path based on video filename (without extension)
                rel_path = os.path.relpath(video_path, root_dir)
                rel_path_no_ext = os.path.splitext(rel_path)[0]
                output_dir = os.path.join(output_root, rel_path_no_ext.replace(os.sep, "_"))
                extract_frames(video_path, output_dir)

# Example usage
if __name__ == "__main__":
    input_dir = "/mnt/c/Users/geets/Downloads/soccernet_videos/england_epl"  # Top-level dir
    output_dir = "./all_frames_output"
    batch_process_videos(input_dir, output_dir)




