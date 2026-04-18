"""Language detection helper."""

from langdetect import detect, LangDetectException


def detect_language(text: str) -> str:
    """Return ISO 639-1 language code, defaulting to 'en' on failure."""
    try:
        return detect(text)
    except LangDetectException:
        return "en"
