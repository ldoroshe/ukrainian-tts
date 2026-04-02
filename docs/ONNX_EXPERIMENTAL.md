# Experimental ONNX backend (espnet_onnx)

The `espnet_onnx` backend is experimental and opt-in. It is designed for
lightweight / mobile inference.

Current project status:

- `espnet_onnx` is faster than classic `espnet` on CPU
- but it currently produces materially lower-fidelity audio for this model
- the default and recommended backend remains `espnet`

In local measurements on Apple Silicon CPU, ONNX was roughly `1.5x` to `1.9x`
faster, but the exported vocoder output lost a large amount of high-frequency
energy and sounded audibly muffled. Use ONNX only for experiments unless you
are actively investigating that fidelity gap.

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

Export now copies files into `./cache/onnx` (instead of symlinking to external
paths) and rewrites absolute paths in `config.yaml` to the local cache path, so
the artifacts are portable across environments including Docker.

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
- Typical RTF on Apple Silicon CPU: approximately `0.17–0.19` on longer text

## Recommended Benchmark Text

Use the same snippet for backend comparisons so quality and timing results are
comparable:

```text
Жодного новонародженого не чекали з таким нетерпінням, як оцього дев'ятиповерхового будинку.
Ще тільки закладався фундамент і копалися траншеї під комунікаційні мережі; ще лише починали зводити стіни й класти перекриття перших поверхів; ще цибатий кран, зіпʼявшись на ноги, примірявся до першого вантажу - так обережно, наче то не цеглини були, а діти, що їх він мав рознести по майбутніх квартирах, ще гори піску, цементу, цегли, арматури і труб захаращували велике подвірʼя, а могутні тягачі-панелевози ревіли натужно, вибехкуючи колії, в яких недовго й шию звернути; ще майбутні вікна й двері темніли порожніми отворами і звідти раз по раз вилітало будівельне сміття; ще навіть не думали про комісію по прийому обʼєкта, яка, заплющивши очі на всі недоробки й упущення, підпише відповідний акт, - будинок лише народжувався: в колотнечі, в сварках, у біганині, у щоденних летючках, у муках, які породіллям і не снились, а майбутні мешканці вже щоденно навідувалися до нього, і чим вище підіймалися поверхи, тим все більше й більше приходило на будівельний майданчик людей.
```

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
conda run -n uktts-onnx python -m pip install --upgrade pip "setuptools<70" wheel
conda run -n uktts-onnx pip install -e .
conda run -n uktts-onnx pip install --force-reinstall torch==2.5.1 torchaudio==2.5.1
conda run -n uktts-onnx pip install \
  "typeguard<3" \
  "scipy<1.12.0" \
  "espnet==202301" \
  "espnet_onnx>=0.2.1" \
  "onnxruntime==1.16.3" \
  "git+https://github.com/savoirfairelinux/num2words.git@3e39091d052829fc9e65c18176ce7b7ff6169772" \
  "ukrainian-word-stress==1.1.0" \
  "git+https://github.com/egorsmkv/ukrainian-accentor.git@5b7971c4e135e3ff3283336962e63fc0b1c80f4c" \
  espnet_model_zoo
conda run -n uktts-onnx pip install --no-deps "onnx==1.13.1"

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
