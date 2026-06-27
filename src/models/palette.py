"""Palette data model."""

from __future__ import annotations

from dataclasses import dataclass
from src.models.circle import RgbColor


@dataclass(frozen=True)
class PaletteColor:
    """A single colour entry in the palette."""
    number: int
    rgb: RgbColor
    hex_color: str
    frequency: int = 0


@dataclass(frozen=True)
class Palette:
    """Ordered collection of palette colours."""
    colors: tuple[PaletteColor, ...]

    def number_for_rgb(self, rgb: RgbColor) -> int:
        """Return the pen number for a given RGB value, or -1 if not found."""
        for color in self.colors:
            if color.rgb == rgb:
                return color.number
        return -1

    def color_for_number(self, number: int) -> PaletteColor | None:
        for color in self.colors:
            if color.number == number:
                return color
        return None

    @property
    def count(self) -> int:
        return len(self.colors)
