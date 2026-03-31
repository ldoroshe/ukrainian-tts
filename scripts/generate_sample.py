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
    return parser.parse_args()


def main():
    from ukrainian_tts.tts import TTS, Voices, Stress
    args = parse_args()

    tts = TTS(device=args.device, backend=args.backend, cache_folder=args.cache_dir)

    samples = [
        "Привіт, як у тебе справи?",
        "Договір підписано 4 квітня 1949 року.",
        "Введіть, будь ласка, св+оє реч+ення.",
    ]

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, s in enumerate(samples, start=1):
        out_path = out_dir / f"sample_{i}.wav"
        with open(out_path, "wb") as fp:
            _, accented = tts.tts(s, Voices.Tetiana.value, Stress.Dictionary.value, fp)
        print(f"Wrote {out_path}  accented_text={accented}")


if __name__ == "__main__":
    main()
