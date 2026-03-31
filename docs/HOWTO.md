# How to Run Ukrainian TTS Locally

This guide covers running both TTS backends from source on macOS with conda.

## Prerequisites

- macOS (Apple Silicon or Intel)
- [conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- Python 3.10 (managed by conda — you don't need to install it separately)
- Docker Desktop (only for `make docker-e2e`)
- Git

## Standard backend (espnet)

The default backend uses the full ESPnet PyTorch runtime.

**1. Set up the environment (once):**

```bash
make setup
```

Creates a `uktts` conda environment and installs all dependencies.

**2. Generate sample WAV files:**

```bash
make run
```

Downloads model artifacts into `./cache/` on first run (may take several minutes).
Output WAV files are written to `./out/`.

**3. Run tests:**

```bash
make test
```

Runs lightweight unit tests — no heavy runtime dependencies required.

## Experimental ONNX backend (espnet_onnx)

See [`docs/ONNX_EXPERIMENTAL.md`](./ONNX_EXPERIMENTAL.md) for the full ONNX guide.

Quick reference:

```bash
make setup-onnx    # one-time env setup
make export-onnx   # one-time ONNX artifact export
make run-onnx      # generate samples
```

## Docker E2E test

Builds a linux/amd64 image and runs the full E2E test inside the container.
This is the most faithful test of the production runtime.

```bash
make docker-e2e
```

First run downloads all model artifacts and wheels — can take 15–60+ minutes.
Subsequent runs are fast due to the `./cache` mount.

## Custom model cache directory

All `make` targets accept `CACHE_DIR` to override the default `./cache`:

```bash
make run       CACHE_DIR=/Volumes/external/tts-models
make run-onnx  CACHE_DIR=/Volumes/external/tts-models
```

## Advanced: raw script flags

`scripts/generate_sample.py` accepts CLI flags directly. All flags override their
corresponding environment variable if both are set.

```
python scripts/generate_sample.py --help
```

```
usage: generate_sample.py [-h] [--device DEVICE] [--backend {espnet,espnet_onnx}]
                           [--cache-dir CACHE_DIR] [--output-dir OUTPUT_DIR]

Generate sample WAV files with Ukrainian TTS.

options:
  --device DEVICE         PyTorch device: cpu, cuda, mps. Overrides $DEVICE. (default: cpu)
  --backend {espnet,espnet_onnx}
                          TTS backend. Overrides $UK_TTS_BACKEND. (default: espnet)
  --cache-dir CACHE_DIR   Path to model artifact directory. Overrides $UK_TTS_CACHE. (default: ./cache)
  --output-dir OUTPUT_DIR Directory to write output WAV files. (default: ./out)
```

**Environment variables (for scripts that don't support flags):**

| Variable | Default | Description |
|---|---|---|
| `DEVICE` | `cpu` | PyTorch device |
| `UK_TTS_BACKEND` | `espnet` | TTS backend |
| `UK_TTS_CACHE` | `./cache` | Model artifact directory |

## Conda environment reference

| Environment | Used for |
|---|---|
| `uktts` | Standard espnet backend |
| `uktts-onnx` | Experimental espnet_onnx backend |

Environments are created by `make setup` / `make setup-onnx`.
To remove and recreate: `conda env remove -n uktts && make setup`
