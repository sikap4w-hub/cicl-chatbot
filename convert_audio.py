import os
import subprocess

raw_dir = "raw_audio"      # dito nakalagay ang mga .m4a
out_dir = "data"           # dito mapupunta ang mga .wav
os.makedirs(out_dir, exist_ok=True)

files = [f for f in os.listdir(raw_dir) if f.lower().endswith(".m4a")]
print(f"Nakita: {len(files)} na .m4a files")

for i, fname in enumerate(files, 1):
    in_path = os.path.join(raw_dir, fname)
    out_name = os.path.splitext(fname)[0] + ".wav"
    out_path = os.path.join(out_dir, out_name)
    subprocess.run([
        "ffmpeg", "-y", "-i", in_path,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        out_path
    ], check=True, capture_output=True)
    print(f"[{i}/{len(files)}] {fname} -> {out_name}")

print("\nTapos na! Nasa 'data' folder ang mga converted na .wav")