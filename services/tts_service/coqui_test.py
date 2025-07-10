from TTS.api import TTS

# Init TTS with multi-speaker English model
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=True)

# List available speakers
print(tts.speakers)

# Use one of the speakers (e.g., 'p225', 'p226', etc.)
tts.tts_to_file(
    text="Welcome to the hackathon!",
    speaker="p301",  # replace with any valid name from tts.speakers
    file_path="test_output.wav"
)
