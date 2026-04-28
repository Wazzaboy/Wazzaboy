from __future__ import annotations

import unicodedata


def normalise_string(value: str) -> str:
    """Normalise a raw string from an HKJC or secondary source.

    Applies Unicode NFC normalisation, replaces non-breaking spaces, and
    collapses all internal whitespace to a single space. Does not alter case.
    """
    if not value:
        return value
    normalised = unicodedata.normalize("NFC", value)
    normalised = normalised.replace("\xa0", " ")
    return " ".join(normalised.split())
