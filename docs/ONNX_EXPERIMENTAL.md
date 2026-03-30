# Experimental ONNX backend (espnet_onnx)

This document describes a known-good local flow for running ukrainian-tts with
the experimental `espnet_onnx` backend.

Important:
- This backend is experimental and opt-in.
- Default backend remains `espnet` for quality parity.
- Use Python 3.10 for best compatibility with espnet/espnet_onnx.

## Apple Silicon local setup (tested)

Create and prepare a dedicated conda environment:

```bash
conda create -y -n uktts-onnx python=3.10
conda run -n uktts-onnx python -m pip install --upgrade pip
```

Install project deps and ONNX extras:

```bash
conda run -n uktts-onnx pip install -e '.[full,onnx]'
```

Install additional exporter/runtime dependencies:

```bash
conda run -n uktts-onnx pip install \
  torchaudio==2.2.2 \
  espnet_model_zoo \
  onnx \
  onnxscript
```

Ensure PyTorch stack is exporter-compatible:

```bash
conda run -n uktts-onnx pip install --force-reinstall torch==2.2.2 torchaudio==2.2.2
```

Export ONNX artifacts into cache:

```bash
mkdir -p cache
conda run -n uktts-onnx env UK_TTS_CACHE="$(pwd)/cache" \
  python scripts/export_espnet_onnx.py --cache-dir "$(pwd)/cache"
```

Run generation with ONNX backend:

```bash
conda run -n uktts-onnx env UK_TTS_CACHE="$(pwd)/cache" UK_TTS_BACKEND=espnet_onnx DEVICE=cpu \
  python scripts/generate_sample.py
```

## What this should produce

- ONNX artifacts linked in `cache/onnx`
- Three generated samples in `/tmp/tts_out` from `scripts/generate_sample.py`
- Typical local RTF (Apple Silicon CPU): around `0.12-0.13` in our validation run

## Troubleshooting

- `No module named torchaudio`: install `torchaudio==2.2.2`.
- `No module named espnet_model_zoo`: install `espnet_model_zoo`.
- `No module named onnx` or `onnxscript`: install both packages.
- ONNX smoke test requires speaker embeddings for this model family; exporter now
  reads one embedding from `spk_xvector.ark` automatically.
