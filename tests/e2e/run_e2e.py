"""E2E runner to be executed inside the Docker image.

This script assumes dependencies (espnet, etc.) are installed inside the image.
It will instantiate real TTS and generate a few samples, then check files.
"""
import os
from pathlib import Path
from ukrainian_tts.tts import TTS, Voices, Stress
import soundfile as sf


def main():
    tts = TTS(device=os.environ.get("DEVICE", "cpu"))
    samples = [
        "Привіт, як у тебе справи?",
        "Договір підписано 4 квітня 1949 року.",
        "Введіть, будь ласка, св+оє реч+ення.",
    ]

    # Prefer persistent cache outputs so files are available on the host when
    # mounting ./cache into the container. This makes it easy to inspect samples
    # after the container exits.
    out_dir = Path(os.environ.get("UK_TTS_CACHE", "/cache")) / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, s in enumerate(samples, start=1):
        out_path = out_dir / f"sample_{i}.wav"
        with open(out_path, "wb") as fp:
            fp, accented = tts.tts(s, Voices.Tetiana.value, Stress.Dictionary.value, fp)
        print(f"Wrote {out_path} accented_text={accented}")
        # basic validation: file exists and readable
        data, sr = sf.read(out_path)
        assert data.size > 10, "Generated audio is too small"
        assert sr > 0

    print("E2E generation OK")


if __name__ == "__main__":
    main()
