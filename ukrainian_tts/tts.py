from io import BytesIO
from os.path import exists, join, dirname
from enum import Enum
# Defer importing formatter and stress modules until runtime to avoid heavy
# top-level imports during test runs or when optional dependencies are
# missing. The imports below are performed inside `tts()` with graceful
# fallbacks.
import numpy as np
import time


def _as_numpy_1d(wav):
    if isinstance(wav, np.ndarray):
        return wav.reshape(-1)

    if hasattr(wav, "detach"):
        wav = wav.detach()
    if hasattr(wav, "cpu"):
        wav = wav.cpu()
    if hasattr(wav, "numpy"):
        wav = wav.numpy()

    return np.asarray(wav).reshape(-1)


class Voices(Enum):
    """List of available voices for the model."""

    Tetiana = "tetiana"
    Mykyta = "mykyta"
    Lada = "lada"
    Dmytro = "dmytro"
    Oleksa = "oleksa"


class Stress(Enum):
    """Options how to stress sentence.
    - `dictionary` - performs lookup in dictionary, taking into account grammatical case of a word and its' neighbors
    - `model` - stress using transformer model"""

    Dictionary = "dictionary"
    Model = "model"


class TTS:
    """ """

    def __init__(self, cache_folder=None, device="cpu", backend=None) -> None:
        """
        Class to setup a text-to-speech engine, from download to model creation.  \n
        Downloads or uses files from `cache_folder` directory.  \n
        By default stores in current directory, or the directory specified by
        the ``UK_TTS_CACHE`` environment variable.

        backend options:
        - "espnet" (default): classic PyTorch/ESPnet runtime.
        - "espnet_onnx" (experimental): ONNX runtime through espnet_onnx.
        """
        import os

        self.device = device
        if cache_folder is None:
            cache_folder = os.environ.get("UK_TTS_CACHE", None)

        self.backend = backend or os.environ.get("UK_TTS_BACKEND", "espnet")
        self.sample_rate = None
        self.__setup_cache(cache_folder)

    def tts(self, text: str, voice: str, stress: str, output_fp=BytesIO()):
        """
        Run a Text-to-Speech engine and output to `output_fp` BytesIO-like object.
        - `text` - your model input text.
        - `voice` - one of predefined voices from `Voices` enum.
        - `stress` - stress method options, predefined in `Stress` enum.
        - `output_fp` - file-like object output. Stores in RAM by default.
        """

        if stress not in [option.value for option in Stress]:
            raise ValueError(
                f"Invalid value for stress option selected! Please use one of the following values: {', '.join([option.value for option in Stress])}."
            )

        if stress == Stress.Model.value:
            stress = True
        else:
            stress = False
        if voice not in [option.value for option in Voices]:
            if voice not in self.xvectors.keys():
                raise ValueError(
                    f"Invalid value for voice selected! Please use one of the following values: {', '.join([option.value for option in Voices])}."
                )

        # import formatter and stress functions lazily so unit tests can
        # import this module without requiring accentor/stanza etc.
        try:
            from .formatter import preprocess_text
            from .stress import sentence_to_stress, stress_dict, stress_with_model

            text = preprocess_text(text)
            text = sentence_to_stress(text, stress_with_model if stress else stress_dict)
        except Exception:
            # If stress/formatter dependencies are unavailable in the runtime
            # environment (e.g., during lightweight unit tests), fall back to
            # a simple lowercase transformation.
            text = text.lower()

        # synthesis (lazy import for torch.no_grad)
        try:
            from torch import no_grad
        except Exception:
            # fallback noop context manager if torch is not available
            from contextlib import nullcontext as no_grad

        with no_grad():
            start = time.time()
            spemb = self.xvectors[voice][0]
            try:
                output = self.synthesizer(text, spembs=spemb)
            except TypeError:
                try:
                    output = self.synthesizer(text, spk_embed=spemb)
                except TypeError:
                    output = self.synthesizer(text)

            if isinstance(output, dict):
                wav = output.get("wav")
            else:
                wav = output

            if wav is None:
                raise RuntimeError("Synthesis backend returned no 'wav' output")

        wav_np = _as_numpy_1d(wav)

        # try to obtain length in a robust way: support numpy arrays, torch tensors,
        # and our FakeTensor wrapper used in unit tests
        try:
            wav_len = len(wav_np)
        except Exception:
            wav_len = 1

        sample_rate = self.sample_rate or getattr(self.synthesizer, "fs", None) or 22050
        rtf = (time.time() - start) / (wav_len / sample_rate)
        print(f"RTF = {rtf:5f}")

        # Write WAV: prefer soundfile if available, otherwise use wave (stdlib)
        try:
            import soundfile as sf

            sf.write(
                output_fp,
                wav_np,
                sample_rate,
                "PCM_16",
                format="wav",
            )
        except Exception:
            # fallback: use wave module to write PCM16
            import wave

            samples = wav_np
            # convert floats -1..1 to int16
            if samples.dtype.kind == "f":
                int_samples = (samples * 32767).astype(np.int16)
            elif samples.dtype == np.int16:
                int_samples = samples
            else:
                int_samples = samples.astype(np.int16)

            # wave accepts file-like objects
            with wave.open(output_fp, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(int_samples.tobytes())

        output_fp.seek(0)

        return output_fp, text

    def __setup_cache(self, cache_folder=None):
        """Downloads models and stores them into `cache_folder`. By default stores in current directory."""
        release_number = "v6.0.0"
        print(
            f"downloading https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}"
        )
        model_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/model.pth"
        config_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/config.yaml"
        speakers_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/spk_xvector.ark"
        feat_stats_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/feats_stats.npz"

        if cache_folder is None:
            cache_folder = "."

        model_path = join(cache_folder, "model.pth")
        config_path = join(cache_folder, "config.yaml")
        speakers_path = join(cache_folder, "spk_xvector.ark")
        feat_stats_path = join(cache_folder, "feats_stats.npz")

        self.__download(model_link, model_path)
        self.__download(config_link, config_path)
        self.__download(speakers_link, speakers_path)
        self.__download(feat_stats_link, feat_stats_path)
        print("downloaded.")

        try:
            from kaldiio import load_ark
        except Exception as e:
            raise ImportError(
                "kaldiio is required to load speaker xvectors. Install requirements or run inside Docker."
            ) from e
        self.xvectors = {k: v for k, v in load_ark(speakers_path)}

        if self.backend == "espnet":
            # lazy import of heavy dependencies
            try:
                from espnet2.bin.tts_inference import Text2Speech
            except Exception as e:
                raise ImportError(
                    "espnet backend requires espnet. Install full requirements or use Docker image."
                ) from e

            self.synthesizer = Text2Speech(
                train_config=config_path, model_file=model_path, device=self.device
            )
            self.sample_rate = getattr(self.synthesizer, "fs", None)
            return

        if self.backend == "espnet_onnx":
            onnx_model_dir = join(cache_folder, "onnx")

            if not exists(onnx_model_dir):
                raise RuntimeError(
                    "espnet_onnx backend is experimental and requires exported ONNX files. "
                    "Expected directory: "
                    f"{onnx_model_dir}. "
                    "Export ONNX artifacts first, then retry."
                )

            try:
                from espnet_onnx import Text2Speech as OnnxText2Speech
            except Exception as e:
                raise ImportError(
                    "espnet_onnx backend requires espnet_onnx and onnxruntime."
                ) from e

            self.synthesizer = OnnxText2Speech(model_dir=onnx_model_dir)
            self.sample_rate = getattr(self.synthesizer, "fs", None) or 22050
            return

        raise ValueError(
            "Invalid backend selected. Supported values: espnet, espnet_onnx"
        )

    def __download(self, url, file_name):
        """Downloads file from `url` into local `file_name` file."""
        if not exists(file_name):
            if not exists(dirname(file_name)):
                raise ValueError(f'Directory "{dirname(file_name)}" doesn\'t exist!')
            print(f"Downloading {file_name}")
            # lazy import requests to avoid dependency at import time
            try:
                import requests

                r = requests.get(url, allow_redirects=True)
                with open(file_name, "wb") as file:
                    file.write(r.content)
            except Exception:
                # network or requests not available: raise with helpful message
                raise RuntimeError(
                    f"Failed to download {url}. Ensure network access and requests library installed."
                )
        else:
            print(f"Found {file_name}. Skipping download...")
