"""Tests for generate_sample.py CLI argument parsing.

scripts/ is added to pythonpath in pytest.ini so we can import directly.
The ukrainian_tts import is inside main(), not at module level, so importing
generate_sample here does not require the heavy runtime dependency.
"""
import sys
import generate_sample


def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["generate_sample.py"])
    monkeypatch.delenv("DEVICE", raising=False)
    monkeypatch.delenv("UK_TTS_BACKEND", raising=False)
    monkeypatch.delenv("UK_TTS_CACHE", raising=False)

    args = generate_sample.parse_args()

    assert args.device == "cpu"
    assert args.backend == "espnet"
    assert args.cache_dir == "./cache"
    assert args.output_dir == "./out"


def test_parse_args_custom(monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        ["generate_sample.py", "--backend", "espnet_onnx", "--device", "mps",
         "--cache-dir", "/tmp/c", "--output-dir", "/tmp/o"]
    )

    args = generate_sample.parse_args()

    assert args.device == "mps"
    assert args.backend == "espnet_onnx"
    assert args.cache_dir == "/tmp/c"
    assert args.output_dir == "/tmp/o"
