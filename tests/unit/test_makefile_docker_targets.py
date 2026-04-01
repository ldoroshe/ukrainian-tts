from pathlib import Path


def test_makefile_has_backend_specific_docker_targets():
    makefile = Path(__file__).resolve().parents[2] / "Makefile"
    text = makefile.read_text(encoding="utf-8")

    assert ".PHONY: docker-run-espnet" in text
    assert ".PHONY: docker-run-onnx" in text
    assert "docker-run-espnet: $(CACHE_DIR)" in text
    assert "docker-run-onnx: $(CACHE_DIR)" in text
    assert "--backend espnet" in text
    assert "--backend espnet_onnx" in text
