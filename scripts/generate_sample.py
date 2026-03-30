#!/usr/bin/env python3
"""Simple script to generate sample WAV files using ukrainian_tts TTS.

This script is intended to be run inside the Docker container or locally after
installing dependencies.
"""
import os
from pathlib import Path
from ukrainian_tts.tts import TTS, Voices, Stress


def main():
    device = os.environ.get("DEVICE", "cpu")
    tts = TTS(device=device)
    samples = [
        "Привіт, як у тебе справи?",
        "Договір підписано 4 квітня 1949 року.",
        "Введіть, будь ласка, св+оє реч+ення.",
    ]
    out_dir = Path("/tmp/tts_out")
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, s in enumerate(samples, start=1):
        out_path = out_dir / f"sample_{i}.wav"
        with open(out_path, "wb") as fp:
            _, accented = tts.tts(s, Voices.Tetiana.value, Stress.Dictionary.value, fp)
        print(f"Wrote {out_path} accented_text={accented}")


if __name__ == "__main__":
    main()
