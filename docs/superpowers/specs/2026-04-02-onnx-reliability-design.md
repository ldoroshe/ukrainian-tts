## Summary

Align the ONNX export environment with the working classic ESPnet stack and remove the silent preprocessing fallback in synthesis. The goal is to make backend comparisons reliable so ONNX can be evaluated fairly against the classic PyTorch path.

## Problem

Two issues currently distort ONNX behavior:

1. The ONNX environment installs a newer `espnet` generation than the classic runtime, so export/runtime behavior can drift from the checkpoint's expected stack.
2. `ukrainian_tts/tts.py` silently falls back to `text.lower()` when formatter or stress preprocessing fails, which changes the input text and makes backend comparisons misleading.

## Design

### 1. Pin ONNX setup to the classic ESPnet line

Update `Makefile` `setup-onnx` so the ONNX environment uses the same ESPnet generation as the working classic stack instead of inheriting a newer one from `.[full,onnx]`.

Intended effect:

- reduce export/runtime mismatch risk
- keep the ONNX experiment as close as possible to the proven classic pipeline

### 2. Fail fast on preprocessing errors

Update `ukrainian_tts/tts.py` so formatter/stress setup failures no longer silently degrade synthesis.

New behavior:

- if formatter or stress preprocessing cannot run, raise a clear runtime error
- the error should explain that degraded fallback is intentionally disabled because reliable backend comparisons require the same normalized/accented input text

This is intentionally strict. If ONNX cannot run reliably under the same preprocessing assumptions as the classic backend, we should detect that immediately.

## Alternatives Considered

### Warn and keep fallback

Rejected because runs would still appear successful while producing materially different input text and therefore different speech timing.

### Add parity tests now

Useful later, but larger than necessary for the immediate fix. The first step is removing environmental drift and hidden fallback.

## Verification

After implementation:

1. Recreate or update the ONNX environment.
2. Run `make export-onnx`.
3. Run `make run` and `make run-onnx`.
4. Confirm preprocessing succeeds explicitly instead of falling back silently.
5. If ONNX quality is still worse, treat the remaining issue as an ONNX vocoder/export problem rather than a preprocessing or version-skew problem.

## Scope

In scope:

- `Makefile` ONNX dependency alignment
- `ukrainian_tts/tts.py` preprocessing failure behavior

Out of scope:

- fixing the remaining ONNX vocoder mismatch
- broader refactoring of the synthesis pipeline
- adding new CLI flags for degraded fallback behavior
