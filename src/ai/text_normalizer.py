from __future__ import annotations

import re
import unicodedata

# Arabic harakat (diacritics) regex
ARABIC_HARAKAT_RE = re.compile(r"[\u064B-\u0652\u0670\u0640]")  # includes tatweel \u0640

# Arabic punctuation to standard spaces or empty
ARABIC_PUNCTUATION_TRANS = str.maketrans("،؟؛", "   ")

# Common OCR character replacements for numeric & code matching
OCR_DIGIT_MAP = str.maketrans({
    "O": "0", "o": "0",
    "I": "1", "l": "1", "|": "1",
    "S": "5", "s": "5",
    "B": "8",
})


def remove_french_diacritics(text: str) -> str:
    """Removes French accents and diacritics (e.g. é -> e, à -> a, ç -> c)."""
    nfd_form = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd_form if unicodedata.category(c) != "Mn")


def normalize_arabic(text: str) -> str:
    """
    Normalizes Arabic text:
    - Removes harakat (tashkeel) and tatweel (kashida).
    - Replaces alef variants (أ, إ, آ, ٱ) with plain alef (ا).
    - Replaces teh marbuta (ة) with heh (ه).
    - Replaces alef maksura (ى) with yeh (ي).
    - Translates Arabic punctuation (، ؟ ؛) to spaces.
    """
    if not text:
        return ""

    # Remove harakat and tatweel
    text = ARABIC_HARAKAT_RE.sub("", text)

    # Translate Arabic punctuation
    text = text.translate(ARABIC_PUNCTUATION_TRANS)

    # Normalize letter forms
    text = re.sub(r"[أإآٱ]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)

    return text


def normalize_ocr_confusions(text: str) -> str:
    """Normalizes typical OCR letter/digit confusions."""
    return text.translate(OCR_DIGIT_MAP)


def normalize_text(text: str, *, remove_accents: bool = True, normalize_ar: bool = True) -> str:
    """
    Full text normalization pipeline:
    1. Lowercase & strip
    2. Arabic normalization (if applicable)
    3. French accent removal (if applicable)
    4. Space collapsing
    """
    if not text:
        return ""

    normalized = text.lower()

    if normalize_ar:
        normalized = normalize_arabic(normalized)

    if remove_accents:
        normalized = remove_french_diacritics(normalized)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized
