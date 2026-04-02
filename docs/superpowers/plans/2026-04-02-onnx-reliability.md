# ONNX Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the ONNX setup with the classic ESPnet stack and make preprocessing failures explicit so backend comparisons are reliable.

**Architecture:** Keep the implementation minimal. Update dependency installation in `Makefile` so the ONNX export environment uses the same ESPnet generation as the classic stack, then change `ukrainian_tts/tts.py` so preprocessing errors raise a clear runtime error instead of silently changing the text. Add focused tests around the new preprocessing behavior.

**Tech Stack:** Python, pytest, Makefile, ESPnet, espnet_onnx

---

### Task 1: Add preprocessing failure tests

**Files:**
- Modify: `tests/test_tts.py`
- Test: `tests/test_tts.py`

- [ ] **Step 1: Write the failing tests**

Add these tests to `tests/test_tts.py` after `test_tts`:

```python
def test_tts_requires_preprocessing_dependencies(monkeypatch):
    def fake_setup_cache(self, cache_folder=None):
        self.synthesizer = make_stub_synthesizer()
        self.xvectors = {v.value: (np.zeros((1, 256), dtype=np.float32),) for v in Voices}

    original_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {"ukrainian_tts.formatter", "ukrainian_tts.stress"}:
            raise ImportError("missing preprocessing dependency")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(TTS, "_TTS__setup_cache", fake_setup_cache, raising=False)
    monkeypatch.setattr("builtins.__import__", fake_import)

    tts = TTS()

    with pytest.raises(RuntimeError, match="Preprocessing failed"):
        tts.tts("Привіт", Voices.Dmytro.value, Stress.Dictionary.value, BytesIO())


def test_tts_surfaces_preprocessing_exceptions(monkeypatch):
    def fake_setup_cache(self, cache_folder=None):
        self.synthesizer = make_stub_synthesizer()
        self.xvectors = {v.value: (np.zeros((1, 256), dtype=np.float32),) for v in Voices}

    monkeypatch.setattr(TTS, "_TTS__setup_cache", fake_setup_cache, raising=False)

    def boom(text):
        raise ValueError("formatter exploded")

    monkeypatch.setattr("ukrainian_tts.tts.preprocess_text", boom, raising=False)
    monkeypatch.setattr("ukrainian_tts.tts.sentence_to_stress", lambda text, fn: text, raising=False)
    monkeypatch.setattr("ukrainian_tts.tts.stress_dict", lambda text: text, raising=False)
    monkeypatch.setattr("ukrainian_tts.tts.stress_with_model", lambda text: text, raising=False)

    tts = TTS()

    with pytest.raises(RuntimeError, match="formatter exploded"):
        tts.tts("Привіт", Voices.Dmytro.value, Stress.Dictionary.value, BytesIO())
```

- [ ] **Step 2: Run the test file to verify failure**

Run: `pytest tests/test_tts.py -q`

Expected: failure because `tts.py` still falls back to lowercase instead of raising.

- [ ] **Step 3: Adjust the existing happy-path assertion for strict preprocessing**

Update the current assertion in `test_tts` from:

```python
# We accept both the exact expected accented form or lowercase fallback
assert ("прив+іт" in text) or (text == "привіт")
```

to:

```python
assert "прив+іт" in text
```

- [ ] **Step 4: Re-run the focused test file**

Run: `pytest tests/test_tts.py -q`

Expected: still failing, but only because implementation has not been updated yet.

### Task 2: Make preprocessing failures explicit in synthesis

**Files:**
- Modify: `ukrainian_tts/tts.py`
- Test: `tests/test_tts.py`

- [ ] **Step 1: Update preprocessing handling in `ukrainian_tts/tts.py`**

At module scope near the existing imports, add eager placeholders so tests can monkeypatch them without importing heavy dependencies at module import time:

```python
preprocess_text = None
sentence_to_stress = None
stress_dict = None
stress_with_model = None
```

Then replace the current block inside `TTS.tts()`:

```python
        try:
            from .formatter import preprocess_text
            from .stress import sentence_to_stress, stress_dict, stress_with_model

            text = preprocess_text(text)
            text = sentence_to_stress(
                text, stress_with_model if stress else stress_dict
            )
        except Exception:
            # If stress/formatter dependencies are unavailable in the runtime
            # environment (e.g., during lightweight unit tests), fall back to
            # a simple lowercase transformation.
            text = text.lower()
```

with this implementation:

```python
        try:
            global preprocess_text, sentence_to_stress, stress_dict, stress_with_model

            if preprocess_text is None:
                from .formatter import preprocess_text as _preprocess_text

                preprocess_text = _preprocess_text

            if sentence_to_stress is None or stress_dict is None or stress_with_model is None:
                from .stress import (
                    sentence_to_stress as _sentence_to_stress,
                    stress_dict as _stress_dict,
                    stress_with_model as _stress_with_model,
                )

                sentence_to_stress = _sentence_to_stress
                stress_dict = _stress_dict
                stress_with_model = _stress_with_model

            text = preprocess_text(text)
            text = sentence_to_stress(
                text, stress_with_model if stress else stress_dict
            )
        except Exception as exc:
            raise RuntimeError(
                "Preprocessing failed. Formatter/stress dependencies must work reliably; degraded fallback is disabled."
            ) from exc
```

- [ ] **Step 2: Run the focused preprocessing tests**

Run: `pytest tests/test_tts.py -q`

Expected: PASS

- [ ] **Step 3: Run the broader lightweight unit suite**

Run: `pytest tests/unit -q tests/test_tts.py tests/test_formatter.py tests/test_stress.py`

Expected: PASS

### Task 3: Pin the ONNX environment to the classic ESPnet stack

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Update `setup-onnx` package installation order and pins**

Replace the current `setup-onnx` recipe:

```make
setup-onnx:
	conda create -y -n $(CONDA_ENV_ONNX) python=$(PYTHON_VERSION)
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) python -m pip install --upgrade pip
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install -e '.[full,onnx]'
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install \
		torchaudio==2.2.2 \
		espnet_model_zoo \
		onnx \
		onnxscript
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install --force-reinstall \
		torch==2.2.2 \
		torchaudio==2.2.2
```

with this version:

```make
setup-onnx:
	conda create -y -n $(CONDA_ENV_ONNX) python=$(PYTHON_VERSION)
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) python -m pip install --upgrade pip
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install -e .
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install \
		"typeguard<3" \
		"scipy<1.12.0" \
		"espnet==202301" \
		"espnet_onnx>=0.2.1" \
		"onnxruntime>=1.16.0" \
		espnet_model_zoo \
		onnx \
		onnxscript
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install --force-reinstall \
		torch==2.5.1 \
		torchaudio==2.5.1
```

This keeps the package itself editable, pins `espnet` to the classic line, and preserves the newer Torch version already shown to work with export.

- [ ] **Step 2: Recreate the ONNX environment**

Run: `conda remove -y -n uktts-onnx --all && make setup-onnx`

Expected: environment installs successfully with `espnet==202301`.

- [ ] **Step 3: Verify the installed versions explicitly**

Run: `conda run -n uktts-onnx python -c "import torch, espnet, espnet_onnx, onnxruntime; print(torch.__version__, espnet.__version__, espnet_onnx.__version__, onnxruntime.__version__)"`

Expected: output includes `2.5.1 202301` and prints installed `espnet_onnx` / `onnxruntime` versions.

### Task 4: Verify the reliability changes end to end

**Files:**
- Modify: none
- Test: existing commands only

- [ ] **Step 1: Re-export ONNX artifacts with the pinned environment**

Run: `make export-onnx`

Expected: `ONNX export OK. Artifacts linked at: .../cache/onnx`

- [ ] **Step 2: Verify classic generation still succeeds**

Run: `make run OUTPUT_DIR=./out_plan_classic TEXT="Привіт, як у тебе справи?" FILENAME=sample`

Expected: successful synthesis and a generated WAV file.

- [ ] **Step 3: Verify ONNX generation still succeeds when preprocessing works**

Run: `make run-onnx OUTPUT_DIR=./out_plan_onnx TEXT="Привіт, як у тебе справи?" FILENAME=sample`

Expected: successful synthesis and a generated WAV file.

- [ ] **Step 4: Verify preprocessing no longer degrades silently**

Run this command to simulate missing preprocessing imports:

```bash
conda run -n uktts python -c "import builtins; from io import BytesIO; from ukrainian_tts.tts import TTS, Voices, Stress; orig = builtins.__import__; \
def fake_import(name, globals=None, locals=None, fromlist=(), level=0): \
    if name in {'ukrainian_tts.formatter', 'ukrainian_tts.stress'}: raise ImportError('missing preprocessing dependency'); \
    return orig(name, globals, locals, fromlist, level); \
builtins.__import__ = fake_import; \
t = TTS(); \
t.tts('Привіт', Voices.Dmytro.value, Stress.Dictionary.value, BytesIO())"
```

Expected: command fails with `RuntimeError: Preprocessing failed...` and does not synthesize degraded output.

- [ ] **Step 5: Commit**

```bash
git add Makefile ukrainian_tts/tts.py tests/test_tts.py docs/superpowers/specs/2026-04-02-onnx-reliability-design.md docs/superpowers/plans/2026-04-02-onnx-reliability.md
git commit -m "fix: make ONNX backend comparisons reliable"
```
