import streamlit as st
import os
import json
import tempfile
import shutil
import time
from datetime import datetime
import threading
import queue
import pandas as pd
import base64
from PIL import Image
import io
from kafka import KafkaConsumer, KafkaProducer

KAFKA_TOPICS = ['video-frames', 'commentary-text', 'audio-output']
KAFKA_BOOTSTRAP = 'kafka1:9092,kafka2:9092,kafka3:9092'
SHARED_DIR = "/app/services/shared"
AUDIO_DIR = "/app/audio_output"

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(SHARED_DIR, exist_ok=True)


st.set_page_config(page_title="Video Analysis Dashboard", page_icon="🎩", layout="wide")

for key, default in {
    'processing_status': 'Ready',
    'current_video': None,
    'frames_processed': 0,
    'commentary_data': [],
    'audio_data': [],
    'latest_frame': None,
    'kafka_queue': queue.Queue()
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# main dashboard
st.title("🎮 Video Analysis & Commentary Dashboard") #emoji hunt lol
tab1, tab2, tab3, tab4 = st.tabs(["📄 Upload Video", "📺 Live Feed", "💬 Commentary", "📊 Analytics"])

def start_frame_ingestion(video_path, video_name, fps):
    try:
        shared_dir = "/app/shared_temp"
        if not os.path.exists(shared_dir):
            os.makedirs(shared_dir, mode=0o755)
        
        test_file = os.path.join(shared_dir, ".test_write")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            raise PermissionError(f"Cannot write to shared directory {shared_dir}: {e}")
        
        shared_video_path = os.path.join(shared_dir, video_name)
        
        shutil.copy2(video_path, shared_video_path)
        
        os.chmod(shared_video_path, 0o644)
        
        if not os.path.exists(shared_video_path):
            raise FileNotFoundError(f"File not found after copy: {shared_video_path}")
        
        # Send message to Kafka
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        message = {
            'action': 'process_video',
            'video_path': shared_video_path,
            'video_name': video_name,
            'fps': fps,
            'timestamp': datetime.now().isoformat()
        }

        producer.send('video-processing-requests', message)
        producer.flush()
        producer.close()
        
        return True, "Success"
        
    except Exception as e:
        error_msg = f"Error starting frame ingestion: {str(e)}"
        print(error_msg)
        return False, error_msg

# video upload tab
with tab1:
    st.header("Upload Video for Analysis")
    uploaded_file = st.file_uploader("Choose a video", type=['mp4', 'avi', 'mov', 'mkv'])

    if uploaded_file:
        st.success(f" Video uploaded: {uploaded_file.name}")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"- **Filename:** {uploaded_file.name}")
            st.write(f"- **Size:** {uploaded_file.size / (1024*1024):.2f} MB")
            st.write(f"- **Type:** {uploaded_file.type}")

        with col2:
            fps = st.slider("Frames per second to extract", 0.5, 5.0, 1.0, 0.5)
            st.write("**Status:**")
            st.success("🟢 Ready to process" if st.session_state.processing_status == "Ready"
                       else "🟡 Processing..." if st.session_state.processing_status == "Processing"
                       else f"🔹 {st.session_state.processing_status}")

        st.video(uploaded_file)

        if st.button(" Start Analysis Pipeline"):
            with st.spinner("Starting video processing..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_video_path = tmp_file.name

                    success, message = start_frame_ingestion(temp_video_path, uploaded_file.name, fps)

                    if success:
                        st.session_state.processing_status = "Processing"
                        st.session_state.current_video = uploaded_file.name
                        st.success("Video processing started")
                        st.balloons()
                    else:
                        st.error(f"Failed to start processing: {message}")
                except Exception as e:
                    st.error(f"Failed to start processing: {e}")
                finally:
                    if 'temp_video_path' in locals():
                        os.unlink(temp_video_path)


    else:
        st.info(" Upload a video to begin.")

# live feed tab , idts this works
with tab2:
    st.header("Live Video Analysis")
    if st.session_state.current_video:
        st.write(f"**Video:** {st.session_state.current_video}")
        col1, col2 = st.columns([3, 1])
        if st.session_state.latest_frame:
            with col1:
                st.image(st.session_state.latest_frame['image'], caption=f"Frame {st.session_state.latest_frame['frame_number']}")
            with col2:
                st.metric("Frames Processed", st.session_state.frames_processed)
                st.json(st.session_state.latest_frame['metadata'])
        else:
            st.info("⏳ Waiting for frames...")
    else:
        st.info(" Upload a video to start.")

# commentary tab again dunno 
with tab3:
    st.header("Generated Commentary")
    if st.session_state.commentary_data:
        st.write(f"**Total commentary entries:** {len(st.session_state.commentary_data)}")
        for comment in st.session_state.commentary_data[-5:]:
            with st.expander(f"Frame {comment['frame_number']} - {comment.get('emotion', 'Unknown')}"):
                st.write(f"**Commentary:** {comment.get('commentary', 'No commentary')}")
                st.write(f"**Emotion:** {comment.get('emotion', 'Unknown')}")
                st.write(f"**Timestamp:** {comment.get('timestamp', 'Unknown')}")

                # look for matching audio file
                matching_audio = next(
                    (a for a in st.session_state.audio_data if a.get('frame_number') == comment.get('frame_number')),
                    None
                )
                if matching_audio and 'audio_file' in matching_audio:
                    audio_filename = os.path.basename(matching_audio['audio_file'])
                    full_path = os.path.join(AUDIO_DIR, audio_filename)
                    
                    if os.path.exists(full_path):
                        try:
                            with open(full_path, "rb") as f:
                                audio_bytes = f.read()
                                st.audio(audio_bytes, format="audio/wav")
                        except Exception as e:
                            st.warning(f" Error reading audio file: {e}")
                    else:
                        st.info(" Audio file not found yet...")
                else:
                    st.info("Audio not yet available for this frame.")
    else:
        st.info("💬 Commentary will appear here during processing.")


# analytics tab 
with tab4:
    st.header("Analytics & Insights")
    if st.session_state.commentary_data:
        emotions_df = pd.DataFrame(st.session_state.commentary_data)
        emotion_counts = emotions_df['emotion'].value_counts().reset_index()
        emotion_counts.columns = ['emotion', 'count']
        st.subheader("Emotion Distribution")
        st.bar_chart(emotion_counts.set_index('emotion'))

        st.subheader("Processing Timeline")
        st.dataframe(emotions_df[['frame_number', 'emotion', 'timestamp']])
    else:
        st.info("📊 Analytics will appear after processing begins.")

def test_kafka_connection():
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        producer.close()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)

# debug to test kafka
if st.button("Test Kafka Connection"):
    success, message = test_kafka_connection()
    if success:
        st.success(f" Kafka connection: {message}")
    else:
        st.error(f"Kafka connection failed: {message}")


# kafka consumer thread
def kafka_consumer_thread(q):
    try:
        consumer = KafkaConsumer(
            *KAFKA_TOPICS,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='streamlit_dashboard'
        )
        for message in consumer:
            q.put((message.topic, message.value))
    except Exception as e:
        q.put(("error", str(e)))

# main thread queue processor 
def handle_kafka_messages():
    q = st.session_state.kafka_queue
    while not q.empty():
        topic, msg = q.get()
        if topic == "video-frames":
            try:
                image_data = base64.b64decode(msg['frame_data'])
                image = Image.open(io.BytesIO(image_data))
                st.session_state.latest_frame = {
                    'image': image,
                    'frame_number': msg['frame_number'],
                    'metadata': {
                        'timestamp': msg['timestamp'],
                        'video_path': msg['video_path'],
                        'saved_path': msg.get('saved_path', '')
                    }
                }
                st.session_state.frames_processed += 1
            except Exception as e:
                st.error(f"Frame processing error: {e}")
        elif topic == "commentary-text":
            st.session_state.commentary_data.append(msg)
        elif topic == "audio-output":
            st.session_state.audio_data.append(msg)
        elif topic == "error":
            st.error(f"Kafka Error: {msg}")

# starting kafka thread once
if 'kafka_thread' not in st.session_state:
    thread = threading.Thread(target=kafka_consumer_thread, args=(st.session_state.kafka_queue,), daemon=True)
    st.session_state.kafka_thread = thread
    thread.start()


handle_kafka_messages()

if st.session_state.processing_status == "Processing":
    time.sleep(5)
    st.rerun()
