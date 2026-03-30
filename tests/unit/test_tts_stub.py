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
        def __len__(self):
            return self._arr.shape[0]

    class StubSynth:
        def __init__(self):
            self.fs = fs

        def __call__(self, text, spembs=None):
            # produce a sine wave numpy array wrapped in FakeTensor
            arr = np.sin(np.linspace(0, 2 * np.pi * 440, int(self.fs * length_seconds))).astype(np.float32)
            return {"wav": FakeTensor(arr)}

    return StubSynth()


def test_tts_with_stub(monkeypatch, tmp_path):
    # monkeypatch TTS.__setup_cache to avoid downloads and set synthesizer + xvectors
    def fake_setup_cache(self, cache_folder=None):
        self.synthesizer = make_stub_synthesizer()
        # minimal xvectors structure expected by code: mapping voice -> (vector,)
        # use numpy zeros as placeholder
        self.xvectors = {v.value: (np.zeros((1, 256), dtype=np.float32),) for v in Voices}

    # __setup_cache is a name-mangled private method on the class; set the
    # mangled attribute so monkeypatch works regardless of name-mangling.
    monkeypatch.setattr(TTS, "_TTS__setup_cache", fake_setup_cache, raising=False)

    tts = TTS()
    out_fp = io.BytesIO()
    result_fp, accented = tts.tts("Привіт", Voices.Dmytro.value, Stress.Dictionary.value, out_fp)

    # result_fp should be seekable and contain WAV-like bytes
    result_fp.seek(0)
    data = result_fp.read()
    assert len(data) > 100
    # accented string should contain expected accent marker
    assert "прив" in accented
