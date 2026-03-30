# Docker Quickstart for Ukrainian TTS

Build the image (this does not download model artifacts by default):

```bash
docker build -t ukrainian-tts:dev .
```

Run the sample generator (this will download model files on first run into /cache):

```bash
docker run --rm -v $(pwd)/cache:/cache ukrainian-tts:dev
```

To run the E2E script inside container explicitly:

```bash
docker run --rm -e DEVICE=cpu -v $(pwd)/cache:/cache ukrainian-tts:dev python tests/e2e/run_e2e.py
```

Notes:
- If you want to preload model artifacts into the image to avoid runtime downloads, run the preloading script during build with a build-arg (not implemented by default).
- The CI runs unit tests only; E2E is a manual job due to artifact sizes.

Developer notes (macOS):
- If you only want to run unit tests locally without installing heavy libs (espnet / torch / scipy), use the dev requirements:
  - python -m pip install -r requirements-dev.txt
  - pytest -q
- If you need full runtime installation on macOS, make sure OpenBLAS and other native libraries are installed:
  - brew install openblas libsndfile
  - export OPENBLAS="$(brew --prefix openblas)"
  - export LDFLAGS="-L$OPENBLAS/lib"
  - export CPPFLAGS="-I$OPENBLAS/include"
  - python -m pip install -r requirements.txt
