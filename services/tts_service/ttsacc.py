import whisper
import jiwer

# Load Whisper ASR model
model = whisper.load_model("base")  # Or use "small", "medium" for better accuracy

# Transcribe the generated speech
result = model.transcribe("test_output.wav")
generated_text = result["text"]

# Define the original ground truth
reference_text = "grey bird stands majestically on beach while waves roll in"

# Calculate Word Error Rate
wer_score = jiwer.wer(reference_text.lower(), generated_text.lower())

# Print results
print("Transcribed:", generated_text)
print("Reference:", reference_text)
print("WER:", wer_score)
