import os
import sys
import types
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ukrainian_tts.tts import TTS


def test_setup_cache_initializes_espnet_from_cache_dir(monkeypatch, tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    def fake_download(self, url, file_name):
        Path(file_name).write_bytes(b"dummy")

    monkeypatch.setattr(TTS, "_TTS__download", fake_download, raising=False)

    fake_kaldiio = types.ModuleType("kaldiio")
    fake_kaldiio.load_ark = lambda path: [
        ("voice", np.zeros((1, 256), dtype=np.float32))
    ]
    monkeypatch.setitem(sys.modules, "kaldiio", fake_kaldiio)

    captured = {}

    class FakeText2Speech:
        def __init__(self, train_config, model_file, device):
            captured["cwd"] = os.getcwd()
            captured["train_config"] = train_config
            captured["model_file"] = model_file
            captured["device"] = device
            self.fs = 22050

    fake_tts_module = types.ModuleType("espnet2.bin.tts_inference")
    fake_tts_module.Text2Speech = FakeText2Speech
    monkeypatch.setitem(sys.modules, "espnet2", types.ModuleType("espnet2"))
    monkeypatch.setitem(sys.modules, "espnet2.bin", types.ModuleType("espnet2.bin"))
    monkeypatch.setitem(sys.modules, "espnet2.bin.tts_inference", fake_tts_module)

    TTS(cache_folder=str(cache_dir))

    assert captured["cwd"] == str(cache_dir)
