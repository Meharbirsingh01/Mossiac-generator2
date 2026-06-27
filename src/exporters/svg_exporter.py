"""Print-ready SVG exporter."""

from __future__ import annotations

import logging
from pathlib import Path

import svgwrite

from src.models.circle import Circle
from src.models.page import Layout
from src.utils.labels import palette_label

LOGGER = logging.getLogger(__name__)


class SvgExporter:
    """Export numbered outline circles as scalable vector graphics."""

    def export(
        self,
        circles: tuple[Circle, ...],
        layout: Layout,
        output_path: Path,
        background_rgb: tuple[int, int, int] = (255, 255, 255),
        circle_outline_rgb: tuple[int, int, int] = (25, 25, 25),
        number_rgb: tuple[int, int, int] = (25, 25, 25),
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dwg = svgwrite.Drawing(
            str(output_path),
            size=(f"{layout.page.width_mm}mm", f"{layout.page.height_mm}mm"),
            viewBox=f"0 0 {layout.page.width_mm} {layout.page.height_mm}",
            profile="full",
        )
        dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"
        dwg.add(dwg.rect(insert=(-1, -1), size=(layout.page.width_mm + 2, layout.page.height_mm + 2), fill=_hex(background_rgb)))
        radius = layout.circle_diameter_mm / 2.0
        font_size = max(1.2, min(layout.circle_diameter_mm * 0.28, 2.1))
        stroke_width = max(0.08, layout.circle_diameter_mm * 0.035)
        group = dwg.g(id="numbered-circles")
        for circle in circles:
            group.add(dwg.circle(center=(circle.x_mm, circle.y_mm), r=radius, fill="#FFFFFF", stroke=_hex(circle_outline_rgb), stroke_width=stroke_width))
            if circle.number < 0:
                continue
            group.add(
                dwg.text(
                    palette_label(circle.number),
                    insert=(circle.x_mm, circle.y_mm + font_size * 0.33),
                    text_anchor="middle",
                    font_size=font_size,
                    font_family="Arial, Helvetica, sans-serif",
                    font_weight="400",
                    fill=_hex(number_rgb),
                )
            )
        dwg.add(group)
        dwg.save(pretty=True)
        LOGGER.info("Wrote SVG: %s", output_path)
        return output_path


def _hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
