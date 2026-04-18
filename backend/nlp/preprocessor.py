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
from nltk.stem import PorterStemmer, ISRIStemmer
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
_arabic_stemmer = ISRIStemmer()
_stop_words_en = set(stopwords.words("english"))

# Arabic stop words (common function words)
_stop_words_ar = {
    "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه", "التي", "الذي",
    "وهو", "وهي", "وهم", "أن", "كان", "قد", "لا", "ما", "لم", "كل",
    "هل", "أو", "إذا", "حتى", "بين", "منذ", "خلال", "وكان", "وقد",
    "ثم", "لكن", "بل", "بعد", "قبل", "عند", "أي", "غير", "كما",
}

# Arabic tashkeel (diacritics) pattern
_ARABIC_TASHKEEL = re.compile(r'[\u0617-\u061A\u064B-\u065F]')

# Normalize Arabic alef variants → plain alef
_ARABIC_ALEF = re.compile(r'[آأإ]')
# Normalize Arabic ya variants → plain ya
_ARABIC_YA = re.compile(r'ى')
# Normalize Arabic ta marbuta → ha
_ARABIC_TA = re.compile(r'ة')

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


def _normalize_arabic(text: str) -> str:
    """Normalize Arabic text: remove tashkeel, normalize alef/ya/ta forms."""
    text = _ARABIC_TASHKEEL.sub('', text)
    text = _ARABIC_ALEF.sub('ا', text)
    text = _ARABIC_YA.sub('ي', text)
    text = _ARABIC_TA.sub('ه', text)
    return text


def _is_arabic(text: str) -> bool:
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return arabic_chars > len(text) * 0.3


def preprocess_arabic(text: str, stem: bool = True) -> str:
    """Preprocessing pipeline for Arabic SMS messages."""
    if not isinstance(text, str) or not text.strip():
        return ""

    text = _remove_urls(text)
    text = _remove_phone_numbers(text)
    text = _normalize_arabic(text)
    text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = text.split()
    tokens = [t for t in tokens if t not in _stop_words_ar]

    if stem:
        tokens = [_arabic_stemmer.stem(t) for t in tokens]

    return " ".join(tokens)


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
        tokens = [t for t in tokens if t not in _stop_words_en]

    # 9. Remove purely numeric tokens (leftover digits)
    tokens = [t for t in tokens if not t.isdigit()]

    # 10. Stem
    if stem:
        tokens = [_stemmer.stem(t) for t in tokens]

    return " ".join(tokens)


def preprocess_auto(text: str, stem: bool = True, remove_stops: bool = True) -> str:
    """Auto-detect language and apply the appropriate preprocessing pipeline."""
    if _is_arabic(text):
        return preprocess_arabic(text, stem=stem)
    return preprocess(text, stem=stem, remove_stops=remove_stops)


def preprocess_batch(texts, **kwargs) -> list[str]:
    """Preprocess a list/Series of SMS messages."""
    return [preprocess(t, **kwargs) for t in texts]
