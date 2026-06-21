"""Image loading and enhancement engine."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

from src.config import ImageProcessingSettings
from src.models.page import Layout

LOGGER = logging.getLogger(__name__)


class ImageEngine:
    """Prepare artwork for the mosaic grid."""

    def __init__(self, settings: ImageProcessingSettings) -> None:
        self.settings = settings

    def load(self, image_path: Path) -> Image.Image:
        """Load an image from disk as RGB."""
        if not image_path.exists():
            raise FileNotFoundError(f"Input image does not exist: {image_path}")
        LOGGER.info("Loading image: %s", image_path)
        return Image.open(image_path).convert("RGB")

    def optimize(self, image: Image.Image) -> Image.Image:
        """Apply automatic corrections and edge-preserving cleanup."""
        optimized = ImageOps.exif_transpose(image).convert("RGB")
        if self.settings.auto_brightness:
            optimized = self._auto_brightness(optimized)
        if self.settings.auto_contrast:
            optimized = ImageOps.autocontrast(optimized, cutoff=1)
        if self.settings.edge_preservation or self.settings.denoise:
            optimized = self._edge_preserving_filter(optimized)
        if self.settings.sharpen:
            optimized = optimized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=3))
        return optimized

    def resize_for_layout(self, image: Image.Image, layout: Layout) -> Image.Image:
        """Resize optimized image to one source pixel per printable circle."""
        LOGGER.info("Resizing optimized image to %sx%s grid", layout.columns, layout.rows)
        return image.resize((layout.columns, layout.rows), Image.Resampling.LANCZOS)

    @staticmethod
    def _auto_brightness(image: Image.Image) -> Image.Image:
        grayscale = ImageOps.grayscale(image)
        mean = float(ImageStat.Stat(grayscale).mean[0])
        if mean <= 0:
            return image
        factor = max(0.75, min(1.35, 128.0 / mean))
        return ImageEnhance.Brightness(image).enhance(factor)

    @staticmethod
    def _edge_preserving_filter(image: Image.Image) -> Image.Image:
        smoothed = image.filter(ImageFilter.MedianFilter(size=3))
        return Image.blend(image, smoothed, alpha=0.35)
