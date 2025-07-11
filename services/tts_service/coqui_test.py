from TTS.api import TTS

# Initialize TTS with the multi-speaker English model
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=True, gpu=False)

# Print available speakers
print("Available speakers:", tts.speakers)

# Define the transcript text
text = """
[00:00] Welcome to the live coverage of the game! The players are walking onto the pitch, and the atmosphere is electric here tonight.

[00:10] Kickoff! The match has begun, and the home team starts with possession.

[00:20] Nice early pressure from the away side—number 7 intercepts the pass and looks to drive forward.

[00:35] Brilliant through ball down the right wing! The winger chases it... crosses into the box...

[00:40] Header! Oh, it's just wide of the post! That was the first real chance of the match.

[01:10] A quick counterattack now—number 10 picks up the ball at midfield. He dribbles past one... past two...

[01:20] He shoots... GOAL! A stunning solo run and a clinical finish! The home crowd erupts!

[01:45] Replay shows just how composed he was in front of goal. That’s 1-0 to the home team.

[02:30] The away team is trying to respond. They’re holding possession now, looking to build from the back.

[03:00] And that’s halftime. A tight contest so far, with the home team leading 1-0 thanks to that fantastic solo effort.
"""

# Generate speech and save to file using a specific speaker
tts.tts_to_file(
    text=text,
    speaker="p301",  # Use a valid speaker name from tts.speakers
    file_path="test_output.wav"
)
