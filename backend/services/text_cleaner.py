import re


def clean_text(text: str) -> str:
    """Normalize extracted document text without discarding useful punctuation."""
    return re.sub(r"\s+", " ", (text or "").replace("\x00", " ")).strip()
