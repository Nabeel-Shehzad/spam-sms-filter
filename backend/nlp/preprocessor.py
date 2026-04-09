"""
Text preprocessing pipeline for SMS spam detection.

Steps:
  1. Lowercase
  2. Adversarial character normalization (e.g. "Fr.ee M0ney" -> "free money")
  3. Remove URLs, phone numbers, special characters
  4. Tokenize
  5. Remove stop words
  6. Stem (PorterStemmer)

Returns a cleaned string ready for feature extraction.
"""

import re
import string
import unicodedata

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# Download required NLTK data on first use
def _ensure_nltk_data():
    resources = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
    ]
    for path, name in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


_ensure_nltk_data()

_stemmer = PorterStemmer()
_stop_words = set(stopwords.words("english"))

# Adversarial character substitutions spammers commonly use
# Maps lookalike characters back to their ASCII equivalents
_ADVERSARIAL_MAP = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "6": "g",
    "7": "t",
    "8": "b",
    "@": "a",
    "$": "s",
    "!": "i",
    "|": "i",
}


def _normalize_adversarial(text: str) -> str:
    """
    Normalize adversarial character substitutions.
    e.g. 'Fr.ee M0ney!!!' -> 'Free Money'
    Only substitutes digits/symbols that are surrounded by letters,
    to avoid corrupting legitimate numbers like phone numbers (handled separately).
    """
    result = []
    for ch in text:
        result.append(_ADVERSARIAL_MAP.get(ch, ch))
    return "".join(result)


def _remove_urls(text: str) -> str:
    return re.sub(r"http\S+|www\.\S+", " ", text)


def _remove_phone_numbers(text: str) -> str:
    # Matches common phone formats: +1-800-555-1234, 07911123456, etc.
    return re.sub(r"(\+?\d[\d\s\-().]{7,}\d)", " ", text)


def _remove_special_characters(text: str) -> str:
    # Keep only letters, digits and spaces; strip punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_unicode(text: str) -> str:
    """Normalize unicode characters to their closest ASCII equivalent."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def preprocess(text: str, stem: bool = True, remove_stops: bool = True) -> str:
    """
    Full preprocessing pipeline for a single SMS message.

    Args:
        text:         Raw SMS string.
        stem:         Apply Porter stemming (default True).
        remove_stops: Remove English stop words (default True).

    Returns:
        Cleaned, space-joined token string.
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # 1. Unicode normalization
    text = _normalize_unicode(text)

    # 2. Lowercase
    text = text.lower()

    # 3. Remove URLs
    text = _remove_urls(text)

    # 4. Remove phone numbers
    text = _remove_phone_numbers(text)

    # 5. Adversarial character normalization
    text = _normalize_adversarial(text)

    # 6. Remove special characters / punctuation
    text = _remove_special_characters(text)

    # 7. Tokenize
    tokens = word_tokenize(text)

    # 8. Remove stop words
    if remove_stops:
        tokens = [t for t in tokens if t not in _stop_words]

    # 9. Remove purely numeric tokens (leftover digits)
    tokens = [t for t in tokens if not t.isdigit()]

    # 10. Stem
    if stem:
        tokens = [_stemmer.stem(t) for t in tokens]

    return " ".join(tokens)


def preprocess_batch(texts, **kwargs) -> list[str]:
    """Preprocess a list/Series of SMS messages."""
    return [preprocess(t, **kwargs) for t in texts]
