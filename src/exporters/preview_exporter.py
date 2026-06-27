"""PNG preview exporter."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.models.circle import Circle
from src.models.page import Layout
from src.utils.labels import palette_label

LOGGER = logging.getLogger(__name__)


class PreviewExporter:
    """Render PNG previews of mosaic pages."""

    def export_numbered(
        self,
        circles: tuple[Circle, ...],
        layout: Layout,
        output_path: Path,
        dpi: int = 180,
        background_rgb: tuple[int, int, int] = (0, 0, 0),
        circle_outline_rgb: tuple[int, int, int] = (255, 255, 255),
        number_rgb: tuple[int, int, int] = (255, 255, 255),
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        px_per_mm = dpi / 25.4
        image = Image.new("RGB", (round(layout.page.width_mm * px_per_mm), round(layout.page.height_mm * px_per_mm)), background_rgb)
        draw = ImageDraw.Draw(image)
        radius_px = (layout.circle_diameter_mm / 2.0) * px_per_mm
        stroke_px = max(1, round(layout.circle_diameter_mm * px_per_mm * 0.035))
        font = _load_font(max(10, round(layout.circle_diameter_mm * px_per_mm * 0.32)))
        for circle in circles:
            x_px = circle.x_mm * px_per_mm
            y_px = circle.y_mm * px_per_mm
            bounds = (x_px - radius_px, y_px - radius_px, x_px + radius_px, y_px + radius_px)
            draw.ellipse(bounds, fill=(255, 255, 255), outline=circle_outline_rgb, width=stroke_px)
            if circle.number < 0:
                continue
            label = palette_label(circle.number)
            box = draw.textbbox((0, 0), label, font=font)
            draw.text((x_px - (box[2] - box[0]) / 2, y_px - (box[3] - box[1]) / 2 - box[1]), label, fill=number_rgb, font=font)
        image.save(output_path)
        LOGGER.info("Wrote numbered preview PNG: %s", output_path)
        return output_path

    def export_colored(
        self,
        circles: tuple[Circle, ...],
        layout: Layout,
        output_path: Path,
        dpi: int = 180,
        background_rgb: tuple[int, int, int] = (0, 0, 0),
        show_grid: bool = True,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        px_per_mm = dpi / 25.4
        image = Image.new("RGB", (round(layout.page.width_mm * px_per_mm), round(layout.page.height_mm * px_per_mm)), background_rgb)
        draw = ImageDraw.Draw(image)
        radius_px = (layout.circle_diameter_mm / 2.0) * px_per_mm
        outline = _blend(background_rgb, (255, 255, 255), 0.16)
        for circle in circles:
            x_px = circle.x_mm * px_per_mm
            y_px = circle.y_mm * px_per_mm
            bounds = (x_px - radius_px, y_px - radius_px, x_px + radius_px, y_px + radius_px)
            draw.ellipse(bounds, fill=circle.rgb, outline=outline if show_grid else circle.rgb, width=1)
        image.save(output_path)
        LOGGER.info("Wrote colored preview PNG: %s", output_path)
        return output_path

    def export_image_preview(self, image: Image.Image, output_path: Path, max_width: int = 1600) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        preview = image.convert("RGB").copy()
        if preview.width > max_width:
            height = round(preview.height * (max_width / preview.width))
            preview = preview.resize((max_width, height), Image.Resampling.LANCZOS)
        preview.save(output_path)
        LOGGER.info("Wrote image preview PNG: %s", output_path)
        return output_path


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(a[i] * (1 - amount) + b[i] * amount) for i in range(3))  # type: ignore[return-value]


def _load_font(size_px: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size_px)
    except OSError:
        return ImageFont.load_default()
