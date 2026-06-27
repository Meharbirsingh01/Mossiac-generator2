"""Palette engine — fixed Faber-Castell Connector 25-pen master palette."""

from __future__ import annotations

import logging
import math

from PIL import Image

from src.config import ImageProcessingSettings
from src.models.circle import RgbColor
from src.models.palette import Palette, PaletteColor

LOGGER = logging.getLogger(__name__)

WHITE_RGB: RgbColor = (255, 255, 255)
BLACK_RGB: RgbColor = (30, 30, 30)   # matches pen 0 "Black" in master palette

MASTER_PALETTE: list[tuple[str, RgbColor]] = [
    ("Black",            (30,   30,  30)),   # 0
    ("Dark Brown",       (101,  47,  16)),   # 1
    ("Brown",            (160,  82,  35)),   # 2
    ("Dark Red",         (160,  20,  20)),   # 3
    ("Red",              (218,  28,  28)),   # 4
    ("Orange-Red",       (235,  80,  20)),   # 5
    ("Orange",           (240, 130,   0)),   # 6
    ("Light Orange",     (248, 175,  60)),   # 7
    ("Skin / Peach",     (242, 185, 145)),   # 8
    ("Light Pink",       (242, 170, 185)),   # 9
    ("Pink / Hot Pink",  (225,  60, 130)),   # 10
    ("Magenta",          (200,  20, 110)),   # 11
    ("Yellow",           (255, 218,   0)),   # 12
    ("Yellow-Green",     (168, 214,   0)),   # 13
    ("Light Green",      (80,  190,  60)),   # 14
    ("Green",            (20,  160,  50)),   # 15
    ("Dark Green",       (0,   110,  40)),   # 16
    ("Teal",             (0,   155, 130)),   # 17
    ("Cyan / Turquoise", (0,   195, 210)),   # 18
    ("Sky Blue",         (90,  185, 235)),   # 19
    ("Cornflower Blue",  (60,  120, 210)),   # 20
    ("Blue",             (20,   70, 185)),   # 21
    ("Dark Blue / Navy", (15,   35, 120)),   # 22
    ("Gold",             (195, 155,  20)),   # 23
    ("Dark Grey",        (95,   95,  95)),   # 24
]


class PaletteEngine:
    """Map every image pixel to the fixed 25-pen master palette."""

    def __init__(
        self,
        number_of_colors: int = 25,
        settings: ImageProcessingSettings | None = None,
        white_threshold: int = 245,
        dark_background_threshold: int = 28,
    ) -> None:
        self.settings = (settings or ImageProcessingSettings()).tuned()
        self.white_threshold = white_threshold
        self.dark_background_threshold = dark_background_threshold
        self._palette_lab = [_rgb_to_lab(rgb) for _, rgb in MASTER_PALETTE]

    def reduce(
        self,
        image: Image.Image,
        edge_map: Image.Image | None = None,
    ) -> tuple[Image.Image, Palette]:
        mapped = self._map_to_master(image.convert("RGB"))
        return mapped, self._build_palette(mapped)

    def _map_to_master(self, source: Image.Image) -> Image.Image:
        src_pixels = source.load()
        output = Image.new("RGB", source.size)
        out_pixels = output.load()
        w, h = source.size
        for y in range(h):
            for x in range(w):
                rgb = _rgb(src_pixels[x, y])  # type: ignore[index]
                if is_blank_white(rgb, self.white_threshold):
                    out_pixels[x, y] = WHITE_RGB        # type: ignore[index]
                elif _is_near_black(rgb, self.dark_background_threshold):
                    # Black areas → map to pen 0 (Black) as a COLOURED dot,
                    # not a blank circle. This preserves black backgrounds
                    # and dark outlines in the mosaic.
                    out_pixels[x, y] = MASTER_PALETTE[0][1]  # type: ignore[index]
                else:
                    out_pixels[x, y] = self._nearest(rgb)  # type: ignore[index]
        return output

    def _nearest(self, rgb: RgbColor) -> RgbColor:
        lab = _rgb_to_lab(rgb)
        best_idx, best_dist = 0, float("inf")
        for i, c_lab in enumerate(self._palette_lab):
            d = ((lab[0]-c_lab[0])**2 + (lab[1]-c_lab[1])**2
                 + (lab[2]-c_lab[2])**2)
            if d < best_dist:
                best_dist, best_idx = d, i
        return MASTER_PALETTE[best_idx][1]

    def _build_palette(self, mapped: Image.Image) -> Palette:
        used: set[RgbColor] = set()
        for pixel in mapped.getdata():
            rgb = _rgb(pixel)
            if rgb != WHITE_RGB:
                used.add(rgb)
        colors: list[PaletteColor] = []
        for pen_number, (name, rgb) in enumerate(MASTER_PALETTE):
            if rgb in used:
                hex_str = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
                freq = sum(1 for p in mapped.getdata() if _rgb(p) == rgb)
                colors.append(PaletteColor(pen_number, rgb, hex_str, freq))
        LOGGER.info("Master palette: %d of 25 colours used", len(colors))
        return Palette(colors=tuple(colors))


def is_blank_white(rgb: RgbColor, threshold: int = 245) -> bool:
    if min(rgb) >= threshold:
        return True
    luminance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    chroma = max(rgb) - min(rgb)
    return (luminance >= 200 and chroma <= 35) or (luminance >= 182 and chroma <= 20)

def _is_near_black(rgb: RgbColor, threshold: int = 28) -> bool:
    """Near-black pixels → pen 0 (Black). NOT blank — they are coloured dots."""
    return rgb[0] <= threshold and rgb[1] <= threshold and rgb[2] <= threshold

def _rgb_to_lab(rgb: RgbColor) -> tuple[float, float, float]:
    r, g, b = (ch / 255.0 for ch in rgb)
    def _lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _lin(r), _lin(g), _lin(b)
    x = r*0.4124564 + g*0.3575761 + b*0.1804375
    y = r*0.2126729 + g*0.7151522 + b*0.0721750
    z = r*0.0193339 + g*0.1191920 + b*0.9503041
    x /= 0.95047; z /= 1.08883
    def _f(t):
        return t**(1/3) if t > 0.008856 else 7.787*t + 16/116
    fx, fy, fz = _f(x), _f(y), _f(z)
    return 116*fy - 16, 500*(fx - fy), 200*(fy - fz)

def _rgb(value) -> RgbColor:
    r, g, b = value[:3]
    return int(r), int(g), int(b)
