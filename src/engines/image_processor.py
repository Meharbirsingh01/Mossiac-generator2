"""Image loading and realistic preprocessing engine."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

from src.config import ImageProcessingSettings
from src.models.circle import RgbColor
from src.models.page import Layout

try:
    import cv2
    import numpy as np
    _CV2 = True
except Exception:
    cv2 = None
    np = None
    _CV2 = False

LOGGER = logging.getLogger(__name__)


class ImageEngine:
    """Prepare artwork for realistic mosaic generation."""

    def __init__(self, settings: ImageProcessingSettings) -> None:
        self.settings = settings.tuned()

    def load(self, image_path: Path) -> Image.Image:
        if not image_path.exists():
            raise FileNotFoundError(f"Input image does not exist: {image_path}")
        LOGGER.info("Loading image: %s", image_path)
        return Image.open(image_path).convert("RGB")

    def optimize(self, image: Image.Image) -> Image.Image:
        """Full preprocessing pipeline."""
        base = ImageOps.exif_transpose(image).convert("RGB")
        base = self._limit_processing_size(base)

        if self.settings.subject_fill_zoom and not self.settings.keep_background:
            cropped = self._subject_fill_crop(base)
            if cropped is not base:
                # Scale the cropped subject back up to the processing size
                # so it fills the full grid — this is the key fix.
                base = cropped.resize(
                    (base.width, base.height),
                    Image.Resampling.LANCZOS,
                )
            else:
                base = cropped

        # Light median pass to remove watermark dots and compression noise
        base = self._denoise_light(base)
        base = ImageOps.autocontrast(base, cutoff=self.settings.contrast_cutoff_percent)
        base = self._realistic_preprocess(base)
        base = self._boost_saturation(base, self.settings.saturation_boost)
        return base

    def edge_map(self, image: Image.Image) -> Image.Image:
        gray = ImageOps.grayscale(image)
        if _CV2 and np is not None:
            edges = cv2.Canny(np.asarray(gray), 40, 120)
            return Image.fromarray(edges).filter(ImageFilter.MaxFilter(size=3))
        edges = ImageChops.add(
            gray.filter(ImageFilter.FIND_EDGES),
            gray.filter(ImageFilter.CONTOUR), scale=1.7)
        return ImageOps.autocontrast(edges).filter(ImageFilter.MaxFilter(size=3))

    def resize_for_quality_grid(self, image: Image.Image, layout: Layout) -> Image.Image:
        scale = max(2, self.settings.high_resolution_scale)
        return image.resize(
            (layout.columns * scale, layout.rows * scale),
            Image.Resampling.LANCZOS)

    def sample_candidates_for_layout(self, image: Image.Image, layout: Layout,
                                     edge_map: Image.Image) -> list[Image.Image]:
        modes = ("edge_mean", "dominant", "center", "contrast")
        return [self.sample_for_layout(image, layout, edge_map, mode)
                for mode in modes[: self.settings.candidate_count]]

    def sample_for_layout(self, image: Image.Image, layout: Layout,
                          edge_map: Image.Image | None = None,
                          mode: str = "edge_mean") -> Image.Image:
        target = Image.new("RGB", (layout.columns, layout.rows), "white")
        source = image.convert("RGB")
        edge_source = (edge_map.resize(source.size, Image.Resampling.BICUBIC)
                       if edge_map else None)
        pixels = source.load()
        edge_pixels = edge_source.load() if edge_source else None
        x_scale = source.width / layout.columns
        y_scale = source.height / layout.rows
        for row in range(layout.rows):
            y0 = int(row * y_scale)
            y1 = max(y0 + 1, int((row + 1) * y_scale))
            for column in range(layout.columns):
                x0 = int(column * x_scale)
                x1 = max(x0 + 1, int((column + 1) * x_scale))
                target.putpixel((column, row),
                    self._cell_color(pixels, edge_pixels, x0, y0, x1, y1, mode))
        return target

    def score_grid(self, grid: Image.Image, reference: Image.Image,
                   reference_edges: Image.Image) -> float:
        ref = reference.resize(grid.size, Image.Resampling.LANCZOS).convert("RGB")
        ref_edges = reference_edges.resize(grid.size, Image.Resampling.BICUBIC)
        grid_edges = self.edge_map(grid).resize(grid.size, Image.Resampling.BICUBIC)
        color_error = edge_score = separation = 0.0
        ref_pixels = ref.load()
        grid_pixels = grid.load()
        ref_edge_px = ref_edges.load()
        grid_edge_px = grid_edges.load()
        for y in range(grid.height):
            for x in range(grid.width):
                color_error += _color_distance(
                    _rgb(ref_pixels[x, y]), _rgb(grid_pixels[x, y]))
                edge_score += 1.0 - abs(
                    ref_edge_px[x, y] - grid_edge_px[x, y]) / 255.0  # type: ignore[operator]
                if x > 0:
                    separation += _color_distance(
                        _rgb(grid_pixels[x, y]), _rgb(grid_pixels[x-1, y])) ** 0.5
                if y > 0:
                    separation += _color_distance(
                        _rgb(grid_pixels[x, y]), _rgb(grid_pixels[x, y-1])) ** 0.5
        px = max(1, grid.width * grid.height)
        return (color_error/px) - (edge_score/px)*420 - (separation/px)*0.8

    # ── private ──────────────────────────────────────────────────────────────

    def _subject_fill_crop(self, image: Image.Image) -> Image.Image:
        """
        Detect uniform background and crop it away.
        Returns the original image unchanged if no clear background found.
        The caller resizes the result back to full processing size.
        """
        w, h = image.size
        rgb_pixels = image.load()

        # Sample corners to detect background colour
        margin = max(4, min(w, h) // 25)
        samples = []
        for cy in [margin, h // 4, h - margin]:
            for cx in [margin, w // 4, w - margin]:
                samples.append(_rgb(rgb_pixels[cx, cy]))  # type: ignore[index]

        bg_r = sorted(s[0] for s in samples)[len(samples) // 2]
        bg_g = sorted(s[1] for s in samples)[len(samples) // 2]
        bg_b = sorted(s[2] for s in samples)[len(samples) // 2]
        bg = (bg_r, bg_g, bg_b)
        bg_luma = 0.2126*bg_r + 0.7152*bg_g + 0.0722*bg_b

        # Corner variance: if corners differ a lot, no simple background
        r_var = max(s[0] for s in samples) - min(s[0] for s in samples)
        g_var = max(s[1] for s in samples) - min(s[1] for s in samples)
        b_var = max(s[2] for s in samples) - min(s[2] for s in samples)
        if (r_var + g_var + b_var) / 3 > 70:
            LOGGER.info("No uniform background (high corner variance) — skip crop")
            return image

        chroma = max(bg_r, bg_g, bg_b) - min(bg_r, bg_g, bg_b)
        if bg_luma < 55:      tol = 30
        elif bg_luma > 165:   tol = 40
        elif chroma > 50:     tol = 48
        else:                 tol = 34

        LOGGER.info("Background RGB%s luma=%.0f chroma=%.0f tol=%d", bg, bg_luma, chroma, tol)

        def _is_bg(x: int, y: int) -> bool:
            rgb = _rgb(rgb_pixels[x, y])  # type: ignore[index]
            return (abs(rgb[0]-bg[0])<=tol and abs(rgb[1]-bg[1])<=tol
                    and abs(rgb[2]-bg[2])<=tol)

        sx = max(1, w // 60)
        sy = max(1, h // 60)

        def _bg_row(y: int) -> bool:
            xs = list(range(0, w, sx))
            return sum(1 for x in xs if _is_bg(x, y)) / len(xs) >= 0.85

        def _bg_col(x: int) -> bool:
            ys = list(range(0, h, sy))
            return sum(1 for y in ys if _is_bg(x, y)) / len(ys) >= 0.85

        top = 0
        while top < h - 1 and _bg_row(top):       top += 1
        bottom = h - 1
        while bottom > top + 1 and _bg_row(bottom): bottom -= 1
        left = 0
        while left < w - 1 and _bg_col(left):      left += 1
        right = w - 1
        while right > left + 1 and _bg_col(right):  right -= 1

        mp = max(6, int(min(w, h) * 0.025))
        box = (max(0, left-mp), max(0, top-mp),
               min(w, right+mp), min(h, bottom+mp))
        cw, ch = box[2]-box[0], box[3]-box[1]

        if cw < w * 0.92 or ch < h * 0.92:
            LOGGER.info("Crop: (%d,%d) -> (%d,%d) — will scale back to fill grid",
                        w, h, cw, ch)
            return image.crop(box)

        LOGGER.info("Crop: no significant background margin — using full image")
        return image

    def _denoise_light(self, image: Image.Image) -> Image.Image:
        """
        Very light median filter to remove isolated noise pixels
        (watermark remnants, JPEG compression dots, single-pixel artifacts).
        Does not blur edges — uses size=3 which only affects truly isolated pixels.
        """
        return image.filter(ImageFilter.MedianFilter(size=3))

    def _realistic_preprocess(self, image: Image.Image) -> Image.Image:
        smoothed = self._bilateral(image)
        edge_mask = self.edge_map(image).point(lambda v: min(255, int(v * 2.0)))
        sharpened = image.filter(
            ImageFilter.UnsharpMask(radius=1.2, percent=150, threshold=2))
        return Image.composite(sharpened, smoothed, edge_mask)

    def _boost_saturation(self, image: Image.Image, factor: float) -> Image.Image:
        if abs(factor - 1.0) < 0.01:
            return image
        return ImageEnhance.Color(image).enhance(factor)

    def _limit_processing_size(self, image: Image.Image) -> Image.Image:
        if max(image.size) <= self.settings.max_processing_edge_px:
            return image
        copy = image.copy()
        copy.thumbnail(
            (self.settings.max_processing_edge_px,
             self.settings.max_processing_edge_px),
            Image.Resampling.LANCZOS)
        return copy

    def _bilateral(self, image: Image.Image) -> Image.Image:
        if _CV2 and np is not None:
            arr = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
            filtered = cv2.bilateralFilter(arr, d=7, sigmaColor=55, sigmaSpace=60)
            return Image.fromarray(cv2.cvtColor(filtered, cv2.COLOR_BGR2RGB))
        return Image.blend(image, image.filter(ImageFilter.MedianFilter(size=3)), alpha=0.22)

    def _cell_color(self, pixels, edge_pixels, x0, y0, x1, y1, mode) -> RgbColor:
        totals = [0.0, 0.0, 0.0]
        total_weight = 0.0
        buckets: dict = {}
        cx = (x0 + x1 - 1) / 2
        cy = (y0 + y1 - 1) / 2
        radius = max(1.0, ((x1-x0)**2 + (y1-y0)**2)**0.5 / 2)
        for y in range(y0, y1):
            for x in range(x0, x1):
                rgb = _rgb(pixels[x, y])  # type: ignore[index]
                edge = (0.0 if edge_pixels is None
                        else edge_pixels[x, y] / 255.0)  # type: ignore[index,operator]
                center = 1.0 - min(1.0, (((x-cx)**2+(y-cy)**2)**0.5/radius))
                contrast = abs(_luminance(rgb) - 128) / 128
                weight = 1.0 + edge * 5.5
                if mode == "dominant":
                    key = tuple(ch // 32 for ch in rgb)
                    buckets[key] = buckets.get(key, 0.0) + weight
                elif mode == "center":
                    weight += center * 4.0
                elif mode == "contrast":
                    weight += contrast * 4.5
                else:
                    weight += contrast * 1.6
                for i in range(3):
                    totals[i] += rgb[i] * weight
                total_weight += weight
        if mode == "dominant" and buckets:
            dominant = max(buckets, key=buckets.get)
            return self._bucket_mean(pixels, x0, y0, x1, y1, dominant)
        return tuple(round(v / total_weight) for v in totals)  # type: ignore[return-value]

    @staticmethod
    def _bucket_mean(pixels, x0, y0, x1, y1, bucket) -> RgbColor:
        totals = [0, 0, 0]
        count = 0
        for y in range(y0, y1):
            for x in range(x0, x1):
                rgb = _rgb(pixels[x, y])  # type: ignore[index]
                if tuple(ch // 32 for ch in rgb) == bucket:
                    for i in range(3):
                        totals[i] += rgb[i]
                    count += 1
        if count == 0:
            return 0, 0, 0
        return tuple(round(v / count) for v in totals)  # type: ignore[return-value]


def _rgb(value) -> RgbColor:
    r, g, b = value[:3]
    return int(r), int(g), int(b)

def _luminance(rgb: RgbColor) -> float:
    return 0.2126*rgb[0] + 0.7152*rgb[1] + 0.0722*rgb[2]

def _color_distance(a: RgbColor, b: RgbColor) -> float:
    return (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2
