"""Page layout engine."""

from __future__ import annotations

import logging

from src.config import MosaicSettings, PageSettings
from src.models.page import Layout, Page

LOGGER = logging.getLogger(__name__)


class LayoutEngine:
    """Calculate page geometry and circle coordinates."""

    def __init__(self, page_settings: PageSettings, mosaic_settings: MosaicSettings) -> None:
        self.page_settings = page_settings.normalized()
        self.mosaic_settings = mosaic_settings

    def calculate(self) -> Layout:
        """Calculate rows and columns that fit inside the configured margins."""
        margins = self.page_settings.margins
        page = Page(
            width_mm=self.page_settings.width_mm,
            height_mm=self.page_settings.height_mm,
            margin_top_mm=margins.top_mm,
            margin_bottom_mm=margins.bottom_mm,
            margin_left_mm=margins.left_mm,
            margin_right_mm=margins.right_mm,
        )
        usable_width = page.width_mm - page.margin_left_mm - page.margin_right_mm
        usable_height = page.height_mm - page.margin_top_mm - page.margin_bottom_mm
        pitch = self.mosaic_settings.pitch_mm
        columns = int((usable_width + self.mosaic_settings.circle_gap_mm) // pitch)
        rows = int((usable_height + self.mosaic_settings.circle_gap_mm) // pitch)
        if columns <= 0 or rows <= 0:
            raise ValueError("Page, margins, and circle settings leave no printable grid area.")
        LOGGER.info("Calculated layout: %s columns x %s rows", columns, rows)
        return Layout(
            page=page,
            rows=rows,
            columns=columns,
            circle_diameter_mm=self.mosaic_settings.circle_diameter_mm,
            circle_gap_mm=self.mosaic_settings.circle_gap_mm,
            pitch_mm=pitch,
        )

    def coordinate_for(self, row: int, column: int) -> tuple[float, float]:
        """Return the centre coordinate for a grid cell."""
        layout = self.calculate()
        radius = layout.circle_diameter_mm / 2.0
        x_mm = layout.page.margin_left_mm + radius + (column * layout.pitch_mm)
        y_mm = layout.page.margin_top_mm + radius + (row * layout.pitch_mm)
        return round(x_mm, 3), round(y_mm, 3)
