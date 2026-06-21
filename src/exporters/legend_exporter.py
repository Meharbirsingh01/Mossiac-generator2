"""Color legend exporter."""

from __future__ import annotations

import logging
from colorsys import rgb_to_hsv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.models.palette import Palette, PaletteColor

LOGGER = logging.getLogger(__name__)


class LegendExporter:
    """Render a printable color-number legend."""

    def export(self, palette: Palette, output_path: Path, dpi: int = 180) -> Path:
        """Write a PNG legend page."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        px_per_mm = dpi / 25.4
        width_px = round(210 * px_per_mm)
        margin_px = round(15 * px_per_mm)
        row_height_px = round(10 * px_per_mm)
        header_height_px = round(18 * px_per_mm)
        height_px = max(round(120 * px_per_mm), margin_px * 2 + header_height_px + row_height_px * len(palette.colors))
        image = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(image)
        title_font = _load_font(26)
        header_font = _load_font(18)
        body_font = _load_font(16)
        x_number = margin_px
        x_swatch = margin_px + round(28 * px_per_mm)
        x_color = margin_px + round(50 * px_per_mm)
        y = margin_px
        draw.text((x_number, y), "Color Legend", fill=(17, 17, 17), font=title_font)
        y += header_height_px
        draw.text((x_number, y), "Number", fill=(17, 17, 17), font=header_font)
        draw.text((x_swatch, y), "Color", fill=(17, 17, 17), font=header_font)
        draw.text((x_color, y), "Name / RGB", fill=(17, 17, 17), font=header_font)
        y += round(8 * px_per_mm)
        draw.line((margin_px, y, width_px - margin_px, y), fill=(70, 70, 70), width=2)
        y += round(3 * px_per_mm)
        for color in palette.colors:
            self._draw_row(draw, color, x_number, x_swatch, x_color, y, row_height_px, body_font)
            y += row_height_px
        image.save(output_path)
        LOGGER.info("Wrote legend PNG: %s", output_path)
        return output_path

    @staticmethod
    def _draw_row(
        draw: ImageDraw.ImageDraw,
        color: PaletteColor,
        x_number: int,
        x_swatch: int,
        x_color: int,
        y: int,
        row_height: int,
        font: ImageFont.ImageFont,
    ) -> None:
        swatch_size = max(18, row_height - 12)
        rgb_text = f"{color_name(color.rgb)}  RGB {color.rgb[0]}, {color.rgb[1]}, {color.rgb[2]}"
        draw.text((x_number, y + 4), str(color.number), fill=(17, 17, 17), font=font)
        draw.rectangle(
            (x_swatch, y + 3, x_swatch + swatch_size, y + 3 + swatch_size),
            fill=color.rgb,
            outline=(40, 40, 40),
            width=1,
        )
        draw.text((x_color, y + 4), rgb_text, fill=(17, 17, 17), font=font)


def color_name(rgb: tuple[int, int, int]) -> str:
    """Return a practical color family name for the legend."""
    red, green, blue = rgb
    hue, saturation, value = rgb_to_hsv(red / 255, green / 255, blue / 255)
    hue_degrees = hue * 360
    if value < 0.18:
        return "Black"
    if value > 0.88 and saturation < 0.12:
        return "White"
    if saturation < 0.12:
        if value < 0.38:
            return "Dark Gray"
        if value > 0.72:
            return "Light Gray"
        return "Gray"
    tone = _tone(value)
    if hue_degrees < 15 or hue_degrees >= 345:
        family = "Red"
    elif hue_degrees < 38:
        family = "Orange"
    elif hue_degrees < 65:
        family = "Yellow"
    elif hue_degrees < 155:
        family = "Green"
    elif hue_degrees < 195:
        family = "Teal"
    elif hue_degrees < 245:
        family = "Blue"
    elif hue_degrees < 285:
        return "Purple"
    elif hue_degrees < 345:
        family = "Rose"
    else:
        family = "Color"
    return f"{tone} {family}".strip()


def _tone(value: float) -> str:
    if value < 0.32:
        return "Dark"
    if value > 0.78:
        return "Light"
    return ""


def _load_font(size_px: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size_px)
    except OSError:
        return ImageFont.load_default()
