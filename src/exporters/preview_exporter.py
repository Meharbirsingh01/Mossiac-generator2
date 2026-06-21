"""PNG preview exporter."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.models.circle import Circle
from src.models.page import Layout

LOGGER = logging.getLogger(__name__)


class PreviewExporter:
    """Render PNG previews of mosaic pages."""

    def export_numbered(self, circles: tuple[Circle, ...], layout: Layout, output_path: Path, dpi: int = 180) -> Path:
        """Write a numbered coloring-page PNG preview using millimetre-accurate scaling."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        px_per_mm = dpi / 25.4
        width_px = max(1, round(layout.page.width_mm * px_per_mm))
        height_px = max(1, round(layout.page.height_mm * px_per_mm))
        image = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(image)
        radius_px = (layout.circle_diameter_mm / 2.0) * px_per_mm
        stroke_px = max(1, round(layout.circle_diameter_mm * px_per_mm * 0.045))
        font = _load_font(max(8, round(layout.circle_diameter_mm * px_per_mm * 0.46)))
        for circle in circles:
            x_px = circle.x_mm * px_per_mm
            y_px = circle.y_mm * px_per_mm
            bounds = (
                x_px - radius_px,
                y_px - radius_px,
                x_px + radius_px,
                y_px + radius_px,
            )
            draw.ellipse(bounds, fill="white", outline=(17, 17, 17), width=stroke_px)
            label = str(circle.number)
            label_box = draw.textbbox((0, 0), label, font=font)
            label_width = label_box[2] - label_box[0]
            label_height = label_box[3] - label_box[1]
            draw.text(
                (x_px - (label_width / 2), y_px - (label_height / 2) - label_box[1]),
                label,
                fill=(17, 17, 17),
                font=font,
            )
        image.save(output_path)
        LOGGER.info("Wrote numbered preview PNG: %s", output_path)
        return output_path

    def export_colored(self, circles: tuple[Circle, ...], layout: Layout, output_path: Path, dpi: int = 180) -> Path:
        """Write a colored finished-artwork PNG preview."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        px_per_mm = dpi / 25.4
        width_px = max(1, round(layout.page.width_mm * px_per_mm))
        height_px = max(1, round(layout.page.height_mm * px_per_mm))
        image = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(image)
        radius_px = (layout.circle_diameter_mm / 2.0) * px_per_mm
        for circle in circles:
            x_px = circle.x_mm * px_per_mm
            y_px = circle.y_mm * px_per_mm
            bounds = (
                x_px - radius_px,
                y_px - radius_px,
                x_px + radius_px,
                y_px + radius_px,
            )
            draw.ellipse(bounds, fill=circle.rgb)
        image.save(output_path)
        LOGGER.info("Wrote colored preview PNG: %s", output_path)
        return output_path

    def export(self, circles: tuple[Circle, ...], layout: Layout, output_path: Path, dpi: int = 180) -> Path:
        """Backward-compatible numbered preview export."""
        return self.export_numbered(circles, layout, output_path, dpi)


def _load_font(size_px: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size_px)
    except OSError:
        return ImageFont.load_default()
