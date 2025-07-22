# dummy test fileeeee, tried random speakers for phun

from TTS.api import TTS

print("Available speakers:", tts.speakers)

# multi-speaker English model
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=True, gpu=False)

text = """["Starting the night 10 points behind the leaders Leicester, with 12, left to play...",
    "Is Sterling on the ball for the first time that firmly by Flanagan",
    "Now the reaction first to the touch from Sterling...",
    "There's no better man to go in for a crunching challenge than Flanagan.",
    "Liverpool fans, if they're going to be quiet to start with...",
    "It's been a good week so far for the referee tonight...",
    "And Liverpool have the first opportunity here from the set piece..."
"""

tts.tts_to_file(
    text=text,
    speaker="p301",  
    file_path="test_output.wav"
)

