"""Mosaic circle generation engine."""

from __future__ import annotations

import logging

from PIL import Image

from src.engines.palette_engine import WHITE_RGB, is_blank_white
from src.models.circle import Circle, RgbColor
from src.models.page import Layout
from src.models.palette import Palette

LOGGER = logging.getLogger(__name__)


class MosaicEngine:
    """Generate Circle objects from a reduced-color image."""

    def create_circles(
        self,
        reduced_image: Image.Image,
        layout: Layout,
        palette: Palette,
        dark_background_threshold: int = 28,
    ) -> tuple[Circle, ...]:
        if reduced_image.size != (layout.columns, layout.rows):
            raise ValueError(
                f"Reduced image dimensions must match layout "
                f"({layout.columns}, {layout.rows}); got {reduced_image.size}.")
        radius = layout.circle_diameter_mm / 2.0
        circles: list[Circle] = []
        pixels = reduced_image.load()
        for row in range(layout.rows):
            y_mm = round(layout.page.margin_top_mm + radius + (row * layout.pitch_mm), 3)
            for column in range(layout.columns):
                x_mm = round(layout.page.margin_left_mm + radius + (column * layout.pitch_mm), 3)
                rgb = _norm(pixels[column, row])  # type: ignore[index]
                # White subject areas → blank circle (number = -1, no label)
                if rgb == WHITE_RGB or is_blank_white(rgb):
                    circles.append(Circle(row, column, x_mm, y_mm, WHITE_RGB, -1))
                    continue
                # All other pixels (including black) → coloured circle with pen number
                circles.append(Circle(row, column, x_mm, y_mm, rgb,
                                      palette.number_for_rgb(rgb)))
        LOGGER.info("Generated %d circles", len(circles))
        return tuple(circles)


def _norm(value) -> RgbColor:
    r, g, b = value[:3]
    return int(r), int(g), int(b)
