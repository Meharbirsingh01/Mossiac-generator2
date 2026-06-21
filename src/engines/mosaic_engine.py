"""Mosaic circle generation engine."""

from __future__ import annotations

import logging

from PIL import Image

from src.models.circle import Circle, RgbColor
from src.models.page import Layout
from src.models.palette import Palette

LOGGER = logging.getLogger(__name__)


class MosaicEngine:
    """Generate Circle objects from a reduced-color image."""

    def create_circles(self, reduced_image: Image.Image, layout: Layout, palette: Palette) -> tuple[Circle, ...]:
        """Create one Circle for each printable dot."""
        if reduced_image.size != (layout.columns, layout.rows):
            raise ValueError(
                "Reduced image dimensions must match layout "
                f"({layout.columns}, {layout.rows}); got {reduced_image.size}."
            )
        radius = layout.circle_diameter_mm / 2.0
        circles: list[Circle] = []
        pixels = reduced_image.load()
        for row in range(layout.rows):
            y_mm = round(layout.page.margin_top_mm + radius + (row * layout.pitch_mm), 3)
            for column in range(layout.columns):
                x_mm = round(layout.page.margin_left_mm + radius + (column * layout.pitch_mm), 3)
                rgb = _normalize_rgb(pixels[column, row])
                circles.append(
                    Circle(
                        row=row,
                        column=column,
                        x_mm=x_mm,
                        y_mm=y_mm,
                        rgb=rgb,
                        number=palette.number_for_rgb(rgb),
                    )
                )
        LOGGER.info("Generated %s circle objects", len(circles))
        return tuple(circles)


def _normalize_rgb(value: object) -> RgbColor:
    red, green, blue = value[:3]  # type: ignore[index]
    return int(red), int(green), int(blue)
