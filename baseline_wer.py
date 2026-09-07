import csv
import torch
from transformers import pipeline
from jiwer import wer

device = 0 if torch.cuda.is_available() else -1
print("Device:", "GPU" if device == 0 else "CPU")

print("Loading whisper-small...")
pipe = pipeline(
    task="automatic-speech-recognition",
    model="openai/whisper-small",
    device=device,
    generate_kwargs={"language": "tagalog", "task": "transcribe"},
)

# Basahin ang metadata.csv
rows = []
with open("data/metadata.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

references = []
predictions = []

print(f"\nTinranscribe ang {len(rows)} clips...\n")
for r in rows:
    audio_path = "data/" + r["file_name"]
    ref = r["transcription"]
    pred = pipe(audio_path)["text"].strip()
    references.append(ref.lower())
    predictions.append(pred.lower())
    print(f"{r['file_name']}")
    print(f"  DAPAT : {ref}")
    print(f"  WHISPER: {pred}\n")

score = wer(references, predictions)
print("=" * 50)
print(f"BASELINE WORD ERROR RATE: {score * 100:.1f}%")
print("=" * 50)