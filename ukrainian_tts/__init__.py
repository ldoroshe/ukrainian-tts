"""Top-level package for ukrainian_tts.

Avoid performing heavy side-effects (like downloading stanza models) at import
time. Provide an explicit helper to download models when needed.
"""

def ensure_stanza_models(lang: str = "uk"):
    try:
        import stanza

        stanza.download(lang)
    except Exception:
        # If stanza is unavailable or download fails, don't crash import.
        # Callers that need stanza should handle errors explicitly.
        pass
