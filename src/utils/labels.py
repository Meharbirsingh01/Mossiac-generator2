"""Palette label helpers — supports pen numbers 0-24."""

from __future__ import annotations


def palette_label(number: int) -> str:
    """
    Return printable color code for pen number.
    0-9  -> "0" to "9"
    10+  -> "A", "B", "C" ... (supports up to 35)
    Negative -> blank (white/background circle)
    """
    if number < 0:
        return ""
    if number < 10:
        return str(number)
    return chr(ord("A") + number - 10)
