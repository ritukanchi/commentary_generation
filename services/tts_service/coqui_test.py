from TTS.api import TTS

# Initialize TTS with the multi-speaker English model
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=True, gpu=False)

# Print available speakers
print("Available speakers:", tts.speakers)

# Define the transcript text
# Initialize TTS with the multi-speaker English model
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=True, gpu=False)

# Print available speakers
print("Available speakers:", tts.speakers)

# Define the transcript text
text = """[
  {
    "offset": 0.05,
    "duration": 20.56,
    "commentary": "Starting the night 10 points behind the leaders Leicester, with 12, left to play...",
    "entity": "Starting the night 10 points behind the leaders [team]Leicester[team]...",
    "class": "1/1",
    "clip": "1.avi"
  },
  {
    "offset": 21.52,
    "duration": 4.02,
    "commentary": "Is Sterling on the ball for the first time that firmly by Flanagan",
    "entity": "Is [player]Sterling[player] on the ball for the first time...",
    "class": 1,
    "clip": "2.avi"
  },
  {
    "offset": 26.22,
    "duration": 11.18,
    "commentary": "Now the reaction first to the touch from Sterling...",
    "entity": "Now the reaction first to the touch from [player]Sterling[player]...",
    "class": "1//2",
    "clip": "3.avi"
  },
  {
    "offset": 38.27,
    "duration": 3.49,
    "commentary": "There's no better man to go in for a crunching challenge than Flanagan.",
    "entity": "There's no better man to go in for a crunching challenge than [player]Flanagan[player].",
    "class": 1,
    "clip": "4.avi"
  },
  {
    "offset": 42.92,
    "duration": 6.02,
    "commentary": "Liverpool fans, if they're going to be quiet to start with...",
    "entity": "[team]Liverpool[team] fans, if they're going to be quiet...",
    "class": 1,
    "clip": "5.avi"
  },
  {
    "offset": 53.77,
    "duration": 9.37,
    "commentary": "It's been a good week so far for the referee tonight...",
    "entity": "It's been a good week so far for the referee tonight, [referee]Flanagan[referee]...",
    "class": "1/1",
    "clip": "7.avi"
  },
  {
    "offset": 64.06,
    "duration": 3.5,
    "commentary": "And Liverpool have the first opportunity here from the set piece...",
    "entity": "And [team]Liverpool[team] have the first opportunity here...",
    "class": 2,
    "clip": "8.avi"
  },
  ...
]
"""

# Generate speech and save to file using a specific speaker
tts.tts_to_file(
    text=text,
    speaker="p301",  # Use a valid speaker name from tts.speakers
    file_path="test_output.wav"
)

