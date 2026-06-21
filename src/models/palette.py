"""Palette models."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.circle import RgbColor


@dataclass(frozen=True, slots=True)
class PaletteColor:
    """A numbered color used by a mosaic project."""

    number: int
    rgb: RgbColor
    hex_value: str
    frequency: int


@dataclass(frozen=True, slots=True)
class Palette:
    """Numbered palette generated from an input image."""

    colors: tuple[PaletteColor, ...]

    def number_for_rgb(self, rgb: RgbColor) -> int:
        """Return the legend number for a palette color."""
        for color in self.colors:
            if color.rgb == rgb:
                return color.number
        raise KeyError(f"RGB color is not in palette: {rgb}")
