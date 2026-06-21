"""Adaptive color quantization and palette generation."""

from __future__ import annotations

import logging
from collections import Counter

from PIL import Image

from src.models.circle import RgbColor
from src.models.palette import Palette, PaletteColor

LOGGER = logging.getLogger(__name__)


class PaletteEngine:
    """Reduce image colors and create stable numbered palettes."""

    def __init__(self, number_of_colors: int) -> None:
        if number_of_colors < 2:
            raise ValueError("number_of_colors must be at least 2")
        self.number_of_colors = number_of_colors

    def reduce(self, image: Image.Image) -> tuple[Image.Image, Palette]:
        """Quantize an RGB image with an adaptive palette."""
        LOGGER.info("Reducing image to %s colors", self.number_of_colors)
        quantized_palette = image.convert("RGB").quantize(
            colors=self.number_of_colors,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        )
        quantized = quantized_palette.convert("RGB")
        palette = self._build_palette(quantized)
        return quantized, palette

    @staticmethod
    def _build_palette(quantized: Image.Image) -> Palette:
        counts: Counter[RgbColor] = Counter(
            (int(red), int(green), int(blue))
            for red, green, blue in quantized.getdata()
        )
        sorted_colors = sorted(
            counts.items(),
            key=lambda item: (-item[1], _relative_luminance(item[0]), item[0]),
        )
        colors = tuple(
            PaletteColor(
                number=index,
                rgb=rgb,
                hex_value=f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}",
                frequency=frequency,
            )
            for index, (rgb, frequency) in enumerate(sorted_colors, start=1)
        )
        return Palette(colors=colors)


def _relative_luminance(rgb: RgbColor) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
