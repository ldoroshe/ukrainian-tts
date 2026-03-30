import io
import numpy as np

from ukrainian_tts.tts import TTS, Voices, Stress


def make_stub_synthesizer(fs=22050, length_seconds=1.0):
    class FakeTensor:
        def __init__(self, arr):
            self._arr = arr.astype(np.float32)

        def view(self, *_):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return self._arr

    class StubSynth:
        def __init__(self):
            self.fs = fs

        def __call__(self, text, spembs=None, spk_embed=None):
            arr = np.sin(
                np.linspace(0, 2 * np.pi * 440, int(self.fs * length_seconds))
            ).astype(np.float32)
            return {"wav": FakeTensor(arr)}

    return StubSynth()


def test_backend_env_selection_onnx(monkeypatch):
    def fake_setup_cache(self, cache_folder=None):
        self.synthesizer = make_stub_synthesizer()
        self.sample_rate = 22050
        self.xvectors = {v.value: (np.zeros((1, 256), dtype=np.float32),) for v in Voices}

    monkeypatch.setenv("UK_TTS_BACKEND", "espnet_onnx")
    monkeypatch.setattr(TTS, "_TTS__setup_cache", fake_setup_cache, raising=False)

    tts = TTS()
    assert tts.backend == "espnet_onnx"

    out_fp = io.BytesIO()
    _, text = tts.tts("Привіт", Voices.Tetiana.value, Stress.Dictionary.value, out_fp)
    assert len(out_fp.getvalue()) > 100
    assert "прив" in text


def test_invalid_backend_raises(monkeypatch):
    monkeypatch.setenv("UK_TTS_BACKEND", "invalid_backend")

    def fake_download(self, url, file_name):
        return None

    monkeypatch.setattr(TTS, "_TTS__download", fake_download, raising=False)

    # Avoid import/install requirements for this check by stubbing setup logic
    def fake_setup_cache(self, cache_folder=None):
        raise ValueError(
            "Invalid backend selected. Supported values: espnet, espnet_onnx"
        )

    monkeypatch.setattr(TTS, "_TTS__setup_cache", fake_setup_cache, raising=False)

    try:
        TTS()
        assert False, "Expected ValueError for invalid backend"
    except ValueError as e:
        assert "Invalid backend selected" in str(e)
