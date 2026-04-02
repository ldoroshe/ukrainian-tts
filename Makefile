# Ukrainian TTS — developer convenience targets
# macOS + conda only. See docs/HOWTO.md for full setup guide.
#
# Overridable variables:
#   CACHE_DIR   — path to model artifact directory (default: ./cache)
#   OUTPUT_DIR  — directory to write output WAV files (default: ./out)
#   TEXT        — text to synthesize (default: built-in samples)
#   VOICE       — voice to use: tetiana, mykyta, lada, dmytro, oleksa (default: tetiana)
#   STRESS      — stress method: dictionary, model (default: dictionary)
#   FILENAME    — output filename without extension (default: sample_N.wav)
#
# Examples:
#   make setup
#   make run
#   make run CACHE_DIR=/my/models
#   make run TEXT="Привіт, світе!"
#   make run TEXT="Hello" OUTPUT_DIR=./my-output
#   make run VOICE=dmytro STRESS=model
#   make run TEXT="Привіт" FILENAME=greeting
#   make setup-onnx && make export-onnx && make run-onnx

CACHE_DIR   ?= $(PWD)/cache
OUTPUT_DIR  ?= $(PWD)/out
TEXT        ?=
VOICE       ?=
STRESS      ?=
FILENAME    ?=

PYTHON_VERSION := 3.10
CONDA_ENV      := uktts
CONDA_ENV_ONNX := uktts-onnx

CONDA_RUN      := conda run --no-capture-output -n $(CONDA_ENV)
CONDA_RUN_ONNX := conda run --no-capture-output -n $(CONDA_ENV_ONNX)

.DEFAULT_GOAL := help

# ── Help ──────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "Ukrainian TTS — available targets"
	@echo ""
	@echo "  Standard backend (espnet):"
	@echo "    setup        Create '$(CONDA_ENV)' conda env and install .[full]"
	@echo "    run          Generate sample WAVs using espnet backend"
	@echo "    test         Run quick unit tests (no heavy deps required)"
	@echo "    docker-e2e   Build Docker image and run full E2E test"
	@echo "    docker-run-espnet  Run sample generation in Docker (espnet backend)"
	@echo ""
	@echo "  ONNX backend (espnet_onnx, experimental):"
	@echo "    setup-onnx   Create '$(CONDA_ENV_ONNX)' env and install all ONNX deps"
	@echo "    export-onnx  Export ONNX artifacts from local model files"
	@echo "    run-onnx     Generate sample WAVs using espnet_onnx backend"
	@echo "    docker-run-onnx    Run sample generation in Docker (espnet_onnx backend)"
	@echo ""
	@echo "  Variables:"
	@echo "    CACHE_DIR    Model artifact directory (default: $(CACHE_DIR))"
	@echo "    OUTPUT_DIR   Output directory for WAV files (default: $(OUTPUT_DIR))"
	@echo "    TEXT         Text to synthesize (default: built-in samples)"
	@echo "    VOICE        Voice: tetiana, mykyta, lada, dmytro, oleksa (default: tetiana)"
	@echo "    STRESS       Stress method: dictionary, model (default: dictionary)"
	@echo "    FILENAME     Output filename without extension (default: sample_N.wav)"
	@echo ""

# ── Standard backend ──────────────────────────────────────────────────────────

.PHONY: setup
setup:
	conda create -y -n $(CONDA_ENV) python=$(PYTHON_VERSION)
	conda run --no-capture-output -n $(CONDA_ENV) python -m pip install --upgrade pip
	conda run --no-capture-output -n $(CONDA_ENV) pip install -e '.[full]'
	@echo ""
	@echo "Setup complete. Run 'make run' to generate samples."

.PHONY: run
run: $(CACHE_DIR)
	$(CONDA_RUN) python scripts/generate_sample.py \
		--backend espnet \
		--cache-dir "$(CACHE_DIR)" \
		--output-dir "$(OUTPUT_DIR)" \
		$(if $(TEXT),--text "$(TEXT)",) \
		$(if $(VOICE),--voice "$(VOICE)",) \
		$(if $(STRESS),--stress "$(STRESS)",) \
		$(if $(FILENAME),--filename "$(FILENAME)",)

.PHONY: test
test:
	$(CONDA_RUN) pytest -q

.PHONY: docker-e2e
docker-e2e: $(CACHE_DIR)
	docker buildx build --platform=linux/amd64 -t ukrainian-tts:e2e --load .
	docker run --rm --platform linux/amd64 \
		-e DEVICE=cpu \
		-e UK_TTS_CACHE=/cache \
		-v "$(CACHE_DIR):/cache" \
		ukrainian-tts:e2e python tests/e2e/run_e2e.py

.PHONY: docker-run-espnet
docker-run-espnet: $(CACHE_DIR)
	docker run --rm --platform linux/amd64 \
		-e DEVICE=cpu \
		-e UK_TTS_CACHE=/cache \
		-v "$(CACHE_DIR):/cache" \
		-v "$(OUTPUT_DIR):/app/out" \
		ukrainian-tts:e2e \
		python scripts/generate_sample.py --backend espnet --cache-dir /cache --output-dir /app/out \
		$(if $(TEXT),--text "$(TEXT)",) \
		$(if $(VOICE),--voice "$(VOICE)",) \
		$(if $(STRESS),--stress "$(STRESS)",) \
		$(if $(FILENAME),--filename "$(FILENAME)",)

.PHONY: docker-run-onnx
docker-run-onnx: $(CACHE_DIR)
	docker run --rm --platform linux/amd64 \
		-e DEVICE=cpu \
		-e UK_TTS_CACHE=/cache \
		-v "$(CACHE_DIR):/cache" \
		-v "$(OUTPUT_DIR):/app/out" \
		ukrainian-tts:e2e \
		python scripts/generate_sample.py --backend espnet_onnx --cache-dir /cache --output-dir /app/out \
		$(if $(TEXT),--text "$(TEXT)",) \
		$(if $(VOICE),--voice "$(VOICE)",) \
		$(if $(STRESS),--stress "$(STRESS)",) \
		$(if $(FILENAME),--filename "$(FILENAME)",)

# ── ONNX backend ──────────────────────────────────────────────────────────────

.PHONY: setup-onnx
setup-onnx:
	conda create -y -n $(CONDA_ENV_ONNX) python=$(PYTHON_VERSION)
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) python -m pip install --upgrade pip "setuptools<70" wheel
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install -e .
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install --force-reinstall \
		torch==2.5.1 \
		torchaudio==2.5.1
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install \
		"typeguard<3" \
		"scipy<1.12.0" \
		"espnet==202301" \
		"espnet_onnx>=0.2.1" \
		"onnxruntime==1.16.3" \
		"git+https://github.com/savoirfairelinux/num2words.git@3e39091d052829fc9e65c18176ce7b7ff6169772" \
		"ukrainian-word-stress==1.1.0" \
		"git+https://github.com/egorsmkv/ukrainian-accentor.git@5b7971c4e135e3ff3283336962e63fc0b1c80f4c" \
		espnet_model_zoo
	conda run --no-capture-output -n $(CONDA_ENV_ONNX) pip install --no-deps \
		"onnx==1.13.1"
	@echo ""
	@echo "ONNX setup complete. Run 'make export-onnx' next."

.PHONY: export-onnx
export-onnx: $(CACHE_DIR)
	$(CONDA_RUN_ONNX) python scripts/export_espnet_onnx.py \
		--cache-dir "$(CACHE_DIR)"

.PHONY: run-onnx
run-onnx: $(CACHE_DIR)
	$(CONDA_RUN_ONNX) python scripts/generate_sample.py \
		--backend espnet_onnx \
		--cache-dir "$(CACHE_DIR)" \
		--output-dir "$(OUTPUT_DIR)" \
		$(if $(TEXT),--text "$(TEXT)",) \
		$(if $(VOICE),--voice "$(VOICE)",) \
		$(if $(STRESS),--stress "$(STRESS)",) \
		$(if $(FILENAME),--filename "$(FILENAME)",)

# ── Internal ──────────────────────────────────────────────────────────────────

$(CACHE_DIR):
	mkdir -p "$(CACHE_DIR)"
