"""PDF exporter for generated page images."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

LOGGER = logging.getLogger(__name__)


class PdfExporter:
    """Package rendered page images as print-sized PDF files."""

    def export_image(self, image_path: Path, output_path: Path, dpi: int = 180) -> Path:
        """Write a single image as a PDF page."""
        if not image_path.exists():
            raise FileNotFoundError(f"PDF source image does not exist: {image_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(image_path) as image:
            image.convert("RGB").save(output_path, "PDF", resolution=dpi)
        LOGGER.info("Wrote PDF: %s", output_path)
        return output_path
