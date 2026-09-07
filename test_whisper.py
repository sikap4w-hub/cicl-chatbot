import time
import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
print("Device:", "GPU" if device == 0 else "CPU only")

print("Loading whisper-small (first run downloads ~1 GB, please wait)...")
pipe = pipeline(
    task="automatic-speech-recognition",
    model="openai/whisper-small",
    device=device,
)

audio_url = "https://huggingface.co/datasets/Narsil/asr_dummy/resolve/main/mlk.flac"
print("Transcribing sample audio...")

start = time.time()
result = pipe(audio_url)
elapsed = time.time() - start

print("\n--- TRANSCRIPTION ---")
print(result["text"])
print(f"\nDone in {elapsed:.1f} seconds.")