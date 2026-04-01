#!/usr/bin/env python3
"""Export ukrainian-tts weights to espnet_onnx format.

This script keeps ONNX support experimental and opt-in.
It uses the already-downloaded local artifacts from UK_TTS_CACHE (or --cache-dir)
and writes exported ONNX files into <cache>/onnx.
"""

import argparse
import os
from pathlib import Path
import shutil

from ukrainian_tts.tts import _make_onnx_config_portable


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cache-dir",
        default=os.environ.get("UK_TTS_CACHE", "."),
        help="Directory with model.pth/config.yaml/feats_stats.npz and output onnx/",
    )
    parser.add_argument(
        "--tag-name",
        default="ukrainian-tts-v6-onnx",
        help="Tag name to write into espnet_onnx tag config",
    )
    parser.add_argument(
        "--quantize",
        action="store_true",
        help="Export quantized ONNX models where supported",
    )
    parser.add_argument(
        "--providers",
        default="CPUExecutionProvider",
        help="Comma-separated onnxruntime providers for smoke test",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    cache_dir = Path(args.cache_dir)
    model_path = cache_dir / "model.pth"
    config_path = cache_dir / "config.yaml"

    if not model_path.exists() or not config_path.exists():
        raise FileNotFoundError(
            "Missing model artifacts. Expected model.pth and config.yaml in "
            f"{cache_dir}."
        )

    try:
        from espnet2.bin.tts_inference import Text2Speech as EspnetText2Speech
        from espnet_onnx import Text2Speech as OnnxText2Speech
        from espnet_onnx.export import TTSModelExport
    except Exception as e:
        raise RuntimeError(
            "This script requires espnet, espnet_onnx and onnxruntime installed."
        ) from e

    print(f"Loading ESPnet model from {config_path} / {model_path}")
    text2speech = EspnetText2Speech(
        train_config=str(config_path),
        model_file=str(model_path),
        device="cpu",
    )

    print("Exporting ONNX artifacts...")
    exporter = TTSModelExport()
    exporter.export(text2speech, args.tag_name, quantize=args.quantize)

    onnx_dir = cache_dir / "onnx"
    onnx_dir.mkdir(parents=True, exist_ok=True)

    print("Resolving exported model directory...")
    # espnet_onnx stores exported directories under cache/tag_name
    exported_root = cache_dir / args.tag_name
    if not exported_root.exists():
        exported_root = Path.home() / ".cache" / "espnet_onnx" / args.tag_name
    if not exported_root.exists():
        raise RuntimeError(
            f"Export finished but expected directory was not found: {exported_root}"
        )

    if onnx_dir.exists():
        shutil.rmtree(onnx_dir)
    onnx_dir.mkdir(parents=True, exist_ok=True)

    for p in exported_root.iterdir():
        target = onnx_dir / p.name
        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        if p.is_dir():
            shutil.copytree(p, target)
        else:
            shutil.copy2(p, target)

    _make_onnx_config_portable(onnx_dir)

    providers = [x.strip() for x in args.providers.split(",") if x.strip()]
    print(f"Running ONNX smoke test with providers: {providers}")
    tts_onnx = OnnxText2Speech(model_dir=str(onnx_dir), providers=providers)

    spemb = None
    speakers_path = cache_dir / "spk_xvector.ark"
    if speakers_path.exists():
        try:
            from kaldiio import load_ark

            xvectors = {k: v for k, v in load_ark(str(speakers_path))}
            if xvectors:
                first_key = sorted(xvectors.keys())[0]
                spemb = xvectors[first_key][0]
        except Exception:
            spemb = None

    if spemb is not None:
        out = tts_onnx("привіт", spembs=spemb)
    else:
        out = tts_onnx("привіт")
    if isinstance(out, dict):
        wav = out.get("wav")
    else:
        wav = out
    if wav is None:
        raise RuntimeError("Smoke test failed: ONNX model produced no wav output")

    print(f"ONNX export OK. Artifacts linked at: {onnx_dir}")


if __name__ == "__main__":
    main()
