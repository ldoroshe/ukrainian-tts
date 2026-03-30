import os
import pytest


@pytest.mark.integration
def test_generate_real():
    """Integration test: runs real TTS if dependencies are present.

    This test is skipped if espnet or other heavy dependencies are not installed.
    It is intended to be run inside the Docker image or a fully provisioned dev env.
    """
    try:
        from ukrainian_tts.tts import TTS, Voices, Stress
    except Exception:
        pytest.skip("TTS or its heavy dependencies are not installed")

    device = os.environ.get("DEVICE", "cpu")
    tts = TTS(device=device)
    out_path = "/tmp/tts_integration_test.wav"
    with open(out_path, "wb") as fp:
        _, accented = tts.tts("Привіт, як у тебе справи?", Voices.Tetiana.value, Stress.Dictionary.value, fp)

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 2000
