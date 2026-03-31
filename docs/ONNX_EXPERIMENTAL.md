# Experimental ONNX backend (espnet_onnx)

The `espnet_onnx` backend is experimental and opt-in. It is designed for
lightweight / mobile inference. The default backend remains `espnet` for
quality parity.

Use Python 3.10 for best compatibility with espnet and espnet_onnx.

## Quick start (macOS, conda)

**1. Set up the ONNX environment:**

```bash
make setup-onnx
```

This creates a dedicated `uktts-onnx` conda environment and installs all
required dependencies including the correct pinned torch/torchaudio versions.

**2. Download model artifacts (if you haven't already):**

The ONNX export step requires model files to already be present in `./cache`.
The easiest way to get them is to run the standard backend once — it downloads
them automatically:

```bash
make setup    # if you haven't set up the standard env yet
make run      # downloads model.pth, config.yaml, etc. into ./cache, then generates samples
```

You can skip sample generation and just download with:

```bash
mkdir -p cache
conda run -n uktts python -c "from ukrainian_tts.tts import TTS; TTS(cache_folder='./cache')" 2>/dev/null || true
```

**3. Export ONNX artifacts from your local model files:**

```bash
make export-onnx
```

Reads model artifacts from `./cache` and writes ONNX files into `./cache/onnx`.

**4. Generate samples with the ONNX backend:**

```bash
make run-onnx
```

Output WAV files are written to `./out/`.

**Custom cache directory:**

```bash
make export-onnx CACHE_DIR=/path/to/models
make run-onnx    CACHE_DIR=/path/to/models
```

## Expected output

- ONNX artifacts in `./cache/onnx/`
- Three WAV samples in `./out/`
- Typical RTF on Apple Silicon CPU: `0.12–0.13`

## Troubleshooting

| Error | Fix |
|---|---|
| `No module named torchaudio` | Re-run `make setup-onnx` — it force-reinstalls torchaudio |
| `No module named espnet_model_zoo` | Re-run `make setup-onnx` |
| `No module named onnx` or `onnxscript` | Re-run `make setup-onnx` |
| `RuntimeError: espnet_onnx backend … Expected directory: …/cache/onnx` | Run `make export-onnx` first |
| `FileNotFoundError: Missing model artifacts` | Ensure `./cache/model.pth` and `./cache/config.yaml` exist; check network access |
| ONNX smoke test fails with speaker embedding error | `spk_xvector.ark` must be present in `CACHE_DIR`; it is downloaded automatically |
| Provider error (`CPUExecutionProvider` not found) | Reinstall onnxruntime: `conda run -n uktts-onnx pip install onnxruntime` |

## Advanced: manual steps

If you prefer to run commands directly without `make`:

```bash
# Create environment
conda create -y -n uktts-onnx python=3.10
conda run -n uktts-onnx python -m pip install --upgrade pip

# Install deps
conda run -n uktts-onnx pip install -e '.[full,onnx]'
conda run -n uktts-onnx pip install torchaudio==2.2.2 espnet_model_zoo onnx onnxscript
conda run -n uktts-onnx pip install --force-reinstall torch==2.2.2 torchaudio==2.2.2

# Export
# Prerequisite: model.pth, config.yaml, spk_xvector.ark, feats_stats.npz must
# already be in ./cache. Run 'make run' (standard backend) first if needed.
mkdir -p cache
conda run -n uktts-onnx \
  python scripts/export_espnet_onnx.py --cache-dir "$(pwd)/cache"

# Generate
conda run -n uktts-onnx \
  python scripts/generate_sample.py \
    --backend espnet_onnx \
    --cache-dir "$(pwd)/cache" \
    --output-dir "$(pwd)/out"
```
