from pathlib import Path

from ukrainian_tts.tts import _make_onnx_config_portable


def test_make_onnx_config_portable_rewrites_absolute_paths(tmp_path):
    onnx_dir = tmp_path / "cache" / "onnx"
    full_dir = onnx_dir / "full"
    full_dir.mkdir(parents=True)

    (onnx_dir / "feats_stats.npz").write_bytes(b"stats")
    (full_dir / "tts_model_encoder.onnx").write_bytes(b"encoder")

    old_root = "/Users/someone/.cache/espnet_onnx/ukrainian-tts-v6-onnx"
    config = (
        "normalize:\n"
        f"  stats_file: {old_root}/feats_stats.npz\n"
        "tts_model:\n"
        "  encoder:\n"
        f"    model_path: {old_root}/full/tts_model_encoder.onnx\n"
    )
    (onnx_dir / "config.yaml").write_text(config, encoding="utf-8")

    changed = _make_onnx_config_portable(str(onnx_dir))

    assert changed is True
    rewritten = (onnx_dir / "config.yaml").read_text(encoding="utf-8")
    assert old_root not in rewritten
    assert f"{onnx_dir}/feats_stats.npz" in rewritten
    assert f"{onnx_dir}/full/tts_model_encoder.onnx" in rewritten


def test_make_onnx_config_portable_noop_for_portable_paths(tmp_path):
    onnx_dir = tmp_path / "cache" / "onnx"
    onnx_dir.mkdir(parents=True)

    portable_line = f"normalize:\n  stats_file: {onnx_dir}/feats_stats.npz\n"
    config_path = onnx_dir / "config.yaml"
    config_path.write_text(portable_line, encoding="utf-8")

    changed = _make_onnx_config_portable(str(onnx_dir))

    assert changed is False
    assert config_path.read_text(encoding="utf-8") == portable_line
