"""Page and layout models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Page:
    """Physical page dimensions and margins."""

    width_mm: float
    height_mm: float
    margin_top_mm: float
    margin_bottom_mm: float
    margin_left_mm: float
    margin_right_mm: float


@dataclass(frozen=True, slots=True)
class Layout:
    """Calculated grid geometry for a page."""

    page: Page
    rows: int
    columns: int
    circle_diameter_mm: float
    circle_gap_mm: float
    pitch_mm: float
