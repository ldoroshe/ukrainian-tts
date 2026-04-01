#!/usr/bin/env python3
"""Generate sample WAV files using ukrainian_tts TTS.

Run inside the Docker container or locally after installing dependencies.
Backend and runtime options can be set via flags or environment variables.
Flags take precedence over environment variables.

Examples:
    # standard backend (espnet)
    python scripts/generate_sample.py

    # ONNX backend
    python scripts/generate_sample.py --backend espnet_onnx --cache-dir ./cache

    # GPU
    python scripts/generate_sample.py --device cuda

    # custom voice and stress
    python scripts/generate_sample.py --voice dmytro --stress model

    # custom text with specific output filename
    python scripts/generate_sample.py --text "Привіт" --filename greeting
"""
import argparse
import os
from pathlib import Path
# ukrainian_tts imported inside main() to allow parse_args() to be used
# without the heavy runtime dependency (e.g., in unit tests).


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate sample WAV files with Ukrainian TTS.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("DEVICE", "cpu"),
        help="PyTorch device: cpu, cuda, mps. Overrides $DEVICE.",
    )
    parser.add_argument(
        "--backend",
        default=os.environ.get("UK_TTS_BACKEND", "espnet"),
        choices=["espnet", "espnet_onnx"],
        help="TTS backend. Overrides $UK_TTS_BACKEND.",
    )
    parser.add_argument(
        "--cache-dir",
        default=os.environ.get("UK_TTS_CACHE", "./cache"),
        help="Path to model artifact directory. Overrides $UK_TTS_CACHE.",
    )
    parser.add_argument(
        "--output-dir",
        default="./out",
        # No env-var override: output location is a per-run choice, not deployment config.
        help="Directory to write output WAV files.",
    )
    parser.add_argument(
        "--text",
        default=os.environ.get("UK_TTS_TEXT", ""),
        help="Text to synthesize. Overrides $UK_TTS_TEXT. If empty, uses built-in samples.",
    )
    parser.add_argument(
        "--voice",
        default=os.environ.get("UK_TTS_VOICE", "tetiana"),
        help="Voice to use: tetiana, mykyta, lada, dmytro, oleksa. Overrides $UK_TTS_VOICE.",
    )
    parser.add_argument(
        "--stress",
        default=os.environ.get("UK_TTS_STRESS", "dictionary"),
        choices=["dictionary", "model"],
        help="Stress method. Overrides $UK_TTS_STRESS.",
    )
    parser.add_argument(
        "--filename",
        default=os.environ.get("UK_TTS_FILENAME", ""),
        help="Output filename (without extension). Overrides $UK_TTS_FILENAME. If empty, uses sample_N.wav.",
    )
    return parser.parse_args()


def main():
    from ukrainian_tts.tts import TTS, Voices, Stress
    args = parse_args()

    tts = TTS(device=args.device, backend=args.backend, cache_folder=args.cache_dir)

    samples = (
        [args.text]
        if args.text
        else [
            "Привіт, як у тебе справи?",
            "Договір підписано 4 квітня 1949 року.",
            "Введіть, будь ласка, св+оє реч+ення.",
        ]
    )

    voice = args.voice
    stress = args.stress

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, s in enumerate(samples, start=1):
        if args.filename and len(samples) == 1:
            out_path = out_dir / f"{args.filename}.wav"
        else:
            out_path = out_dir / f"sample_{i}.wav"
        with open(out_path, "wb") as fp:
            _, accented = tts.tts(s, voice, stress, fp)
        print(f"Wrote {out_path}  accented_text={accented}")


if __name__ == "__main__":
    main()
