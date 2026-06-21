"""Filled answer-page exporter."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw

from src.models.circle import Circle, RgbColor
from src.models.page import Layout

LOGGER = logging.getLogger(__name__)


class AnswerExporter:
    """Render the completed colored mosaic answer page."""

    def export(self, circles: tuple[Circle, ...], layout: Layout, output_path: Path, dpi: int = 180) -> Path:
        """Write a filled PNG answer page."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        px_per_mm = dpi / 25.4
        image = Image.new(
            "RGB",
            (round(layout.page.width_mm * px_per_mm), round(layout.page.height_mm * px_per_mm)),
            "white",
        )
        draw = ImageDraw.Draw(image)
        radius_px = (layout.circle_diameter_mm / 2.0) * px_per_mm
        outline_width = max(1, round(layout.circle_diameter_mm * px_per_mm * 0.025))
        for circle in circles:
            x_px = circle.x_mm * px_per_mm
            y_px = circle.y_mm * px_per_mm
            bounds = (
                x_px - radius_px,
                y_px - radius_px,
                x_px + radius_px,
                y_px + radius_px,
            )
            draw.ellipse(bounds, fill=_as_rgb(circle.rgb), outline=(255, 255, 255), width=outline_width)
        image.save(output_path)
        LOGGER.info("Wrote answer PNG: %s", output_path)
        return output_path


def _as_rgb(rgb: RgbColor) -> tuple[int, int, int]:
    return int(rgb[0]), int(rgb[1]), int(rgb[2])
