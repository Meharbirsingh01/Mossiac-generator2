"""Color legend exporter."""

from __future__ import annotations

from colorsys import rgb_to_hsv
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.models.palette import Palette, PaletteColor
from src.utils.labels import palette_label

LOGGER = logging.getLogger(__name__)


class LegendExporter:
    """Render a clean image-specific color legend."""

    def export(self, palette: Palette, output_path: Path, dpi: int = 180) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        px_per_mm = dpi / 25.4
        width_px = round(210 * px_per_mm)
        margin_px = round(15 * px_per_mm)
        title_height = round(18 * px_per_mm)
        row_height = round(8.8 * px_per_mm)
        table_width = width_px - (margin_px * 2)
        height_px = margin_px * 2 + title_height + row_height * (len(palette.colors) + 1)
        image = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(image)
        title_font = _load_font(28)
        header_font = _load_font(18)
        body_font = _load_font(16)
        y = margin_px
        draw.text((margin_px, y), "Color Legend", fill=(17, 17, 17), font=title_font)
        y += title_height
        col_label = margin_px
        col_swatch = margin_px + round(table_width * 0.22)
        col_name = margin_px + round(table_width * 0.46)
        col_end = margin_px + table_width
        self._row_border(draw, margin_px, y, col_end, row_height)
        draw.text((col_label + 10, y + 10), "Code", fill=(17, 17, 17), font=header_font)
        draw.text((col_swatch + 10, y + 10), "Reference Color", fill=(17, 17, 17), font=header_font)
        draw.text((col_name + 10, y + 10), "Color Name", fill=(17, 17, 17), font=header_font)
        y += row_height
        for color in palette.colors:
            self._draw_color_row(draw, color, col_label, col_swatch, col_name, col_end, y, row_height, body_font)
            y += row_height
        image.save(output_path)
        LOGGER.info("Wrote legend PNG: %s", output_path)
        return output_path

    @staticmethod
    def _draw_color_row(
        draw: ImageDraw.ImageDraw,
        color: PaletteColor,
        col_label: int,
        col_swatch: int,
        col_name: int,
        col_end: int,
        y: int,
        row_height: int,
        font: ImageFont.ImageFont,
    ) -> None:
        LegendExporter._row_border(draw, col_label, y, col_end, row_height)
        swatch_size = row_height - 16
        swatch_y = y + 8
        draw.text((col_label + 18, y + 12), palette_label(color.number), fill=(17, 17, 17), font=font)
        draw.rectangle(
            (col_swatch + 12, swatch_y, col_swatch + 12 + swatch_size, swatch_y + swatch_size),
            fill=color.rgb,
            outline=(17, 17, 17),
            width=2,
        )
        draw.text((col_name + 12, y + 12), color_name(color.rgb), fill=(17, 17, 17), font=font)

    @staticmethod
    def _row_border(draw: ImageDraw.ImageDraw, x0: int, y: int, x1: int, row_height: int) -> None:
        draw.rectangle((x0, y, x1, y + row_height), outline=(35, 35, 35), width=2)
        draw.line((x0 + round((x1 - x0) * 0.22), y, x0 + round((x1 - x0) * 0.22), y + row_height), fill=(35, 35, 35), width=2)
        draw.line((x0 + round((x1 - x0) * 0.46), y, x0 + round((x1 - x0) * 0.46), y + row_height), fill=(35, 35, 35), width=2)


def color_name(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    hue, saturation, value = rgb_to_hsv(r / 255, g / 255, b / 255)
    hue *= 360
    if value < 0.18:
        return "Black"
    if value > 0.9 and saturation < 0.12:
        return "White"
    if saturation < 0.14:
        if value < 0.38:
            return "Dark Gray"
        if value > 0.72:
            return "Light Gray"
        return "Gray"
    tone = "Dark " if value < 0.32 else "Light " if value > 0.78 else ""
    if hue < 15 or hue >= 345:
        family = "Red"
    elif hue < 38:
        family = "Orange"
    elif hue < 65:
        family = "Yellow"
    elif hue < 155:
        family = "Green"
    elif hue < 195:
        family = "Teal"
    elif hue < 245:
        family = "Blue"
    elif hue < 285:
        family = "Purple"
    else:
        family = "Pink"
    return f"{tone}{family}"


def _load_font(size_px: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size_px)
    except OSError:
        return ImageFont.load_default()
