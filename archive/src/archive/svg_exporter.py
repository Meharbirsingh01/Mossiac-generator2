"""
svg_exporter.py
Version 1.0

Purpose:
    Export a list of Circle objects to a print-ready SVG.

Expected Circle fields:
    row
    column
    x_mm
    y_mm
    rgb
    number
"""

import svgwrite


MM_TO_PX = 3.7795275591


def mm_to_px(value_mm: float) -> float:
    return value_mm * MM_TO_PX


def export_svg(
    circles,
    output_file,
    page_width_mm,
    page_height_mm,
    circle_diameter_mm,
):
    """
    Export circles to an SVG.

    Parameters
    ----------
    circles : list[Circle]
    output_file : str
    page_width_mm : float
    page_height_mm : float
    circle_diameter_mm : float
    """

    dwg = svgwrite.Drawing(
        output_file,
        size=(
            f"{page_width_mm}mm",
            f"{page_height_mm}mm",
        ),
    )

    radius_px = mm_to_px(circle_diameter_mm / 2)

    font_size = max(6, radius_px * 0.9)

    for circle in circles:

        x = mm_to_px(circle.x_mm)
        y = mm_to_px(circle.y_mm)

        dwg.add(
            dwg.circle(
                center=(x, y),
                r=radius_px,
                fill="white",
                stroke="black",
                stroke_width=0.6,
            )
        )

        dwg.add(
            dwg.text(
                str(circle.number),
                insert=(x, y + font_size * 0.32),
                text_anchor="middle",
                font_size=font_size,
                font_family="Arial",
                fill="black",
            )
        )

    dwg.save()

    print(f"SVG exported -> {output_file}")
