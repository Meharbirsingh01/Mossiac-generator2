"""Printable circle model."""

from __future__ import annotations

from dataclasses import dataclass


RgbColor = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class Circle:
    """A single printable mosaic dot."""

    row: int
    column: int
    x_mm: float
    y_mm: float
    rgb: RgbColor
    number: int
