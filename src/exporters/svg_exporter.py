"""Print-ready SVG exporter."""

from __future__ import annotations

import logging
from pathlib import Path

import svgwrite

from src.models.circle import Circle
from src.models.page import Layout

LOGGER = logging.getLogger(__name__)


class SvgExporter:
    """Export numbered outline circles as scalable vector graphics."""

    def export(self, circles: tuple[Circle, ...], layout: Layout, output_path: Path) -> Path:
        """Write a print-ready coloring page SVG."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dwg = svgwrite.Drawing(
            str(output_path),
            size=(f"{layout.page.width_mm}mm", f"{layout.page.height_mm}mm"),
            viewBox=f"0 0 {layout.page.width_mm} {layout.page.height_mm}",
            profile="full",
        )
        dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"
        dwg.add(
            dwg.rect(
                insert=(0, 0),
                size=(layout.page.width_mm, layout.page.height_mm),
                fill="white",
            )
        )
        radius = layout.circle_diameter_mm / 2.0
        font_size = max(0.9, min(layout.circle_diameter_mm * 0.34, 1.35))
        stroke_width = max(0.12, layout.circle_diameter_mm * 0.045)
        group = dwg.g(id="numbered-circles")
        for circle in circles:
            group.add(
                dwg.circle(
                    center=(circle.x_mm, circle.y_mm),
                    r=radius,
                    fill="white",
                    stroke="#111111",
                    stroke_width=stroke_width,
                )
            )
            group.add(
                dwg.text(
                    str(circle.number),
                    insert=(circle.x_mm, circle.y_mm + (font_size * 0.33)),
                    text_anchor="middle",
                    font_size=font_size,
                    font_family="Arial, Helvetica, sans-serif",
                    font_weight="400",
                    fill="#111111",
                )
            )
        dwg.add(group)
        dwg.save(pretty=True)
        LOGGER.info("Wrote SVG: %s", output_path)
        return output_path
