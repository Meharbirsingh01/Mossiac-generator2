"""Filled answer-page exporter."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw

from src.models.circle import Circle
from src.models.page import Layout

LOGGER = logging.getLogger(__name__)


class AnswerExporter:
    """Render the completed colored mosaic answer page."""

    def export(
        self,
        circles: tuple[Circle, ...],
        layout: Layout,
        output_path: Path,
        dpi: int = 180,
        background_rgb: tuple[int, int, int] = (0, 0, 0),
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        px_per_mm = dpi / 25.4
        image = Image.new("RGB", (round(layout.page.width_mm * px_per_mm), round(layout.page.height_mm * px_per_mm)), background_rgb)
        draw = ImageDraw.Draw(image)
        radius_px = (layout.circle_diameter_mm / 2.0) * px_per_mm
        outline = _blend(background_rgb, (255, 255, 255), 0.14)
        for circle in circles:
            x_px = circle.x_mm * px_per_mm
            y_px = circle.y_mm * px_per_mm
            bounds = (x_px - radius_px, y_px - radius_px, x_px + radius_px, y_px + radius_px)
            draw.ellipse(bounds, fill=circle.rgb, outline=outline, width=1)
        image.save(output_path)
        LOGGER.info("Wrote answer PNG: %s", output_path)
        return output_path


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(a[i] * (1 - amount) + b[i] * amount) for i in range(3))  # type: ignore[return-value]
