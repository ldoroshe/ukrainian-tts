# Ukrainian TTS — developer convenience targets
# macOS + conda only. See docs/HOWTO.md for full setup guide.
#
# Overridable variables:
#   CACHE_DIR  — path to model artifact directory (default: ./cache)
#
# Examples:
#   make setup
#   make run
#   make run CACHE_DIR=/my/models
#   make setup-onnx && make export-onnx && make run-onnx

CACHE_DIR ?= $(PWD)/cache

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
	@echo ""
	@echo "  ONNX backend (espnet_onnx, experimental):"
	@echo "    setup-onnx   Create '$(CONDA_ENV_ONNX)' env and install all ONNX deps"
	@echo "    export-onnx  Export ONNX artifacts from local model files"
	@echo "    run-onnx     Generate sample WAVs using espnet_onnx backend"
	@echo ""
	@echo "  Variables:"
	@echo "    CACHE_DIR    Model artifact directory (default: $(CACHE_DIR))"
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
		--output-dir "$(PWD)/out"

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

# ── ONNX backend ──────────────────────────────────────────────────────────────

.PHONY: setup-onnx
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
		--output-dir "$(PWD)/out"

# ── Internal ──────────────────────────────────────────────────────────────────

$(CACHE_DIR):
	mkdir -p "$(CACHE_DIR)"
