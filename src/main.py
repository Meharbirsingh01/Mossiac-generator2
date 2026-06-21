"""Command-line entry point for MosaicGenerator Version 0.3."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import AppConfig, MosaicSettings, PageSettings
from src.engines.image_processor import ImageEngine
from src.engines.layout_engine import LayoutEngine
from src.engines.mosaic_engine import MosaicEngine
from src.engines.palette_engine import PaletteEngine
from src.exporters.answer_exporter import AnswerExporter
from src.exporters.legend_exporter import LegendExporter
from src.exporters.pdf_exporter import PdfExporter
from src.exporters.preview_exporter import PreviewExporter
from src.exporters.project_exporter import ProjectExporter
from src.exporters.svg_exporter import SvgExporter
from src.models.project import Project

LOGGER = logging.getLogger(__name__)


def build_project(config: AppConfig, image_path: Path) -> Project:
    """Run the full image-to-circles pipeline."""
    layout = LayoutEngine(config.page, config.mosaic).calculate()
    image_engine = ImageEngine(config.image_processing)
    source_image = image_engine.load(image_path)
    optimized_image = image_engine.optimize(source_image)
    grid_image = image_engine.resize_for_layout(optimized_image, layout)
    reduced_image, palette = PaletteEngine(config.mosaic.number_of_colors).reduce(grid_image)
    circles = MosaicEngine().create_circles(reduced_image, layout, palette)
    return Project(
        name=config.project_name,
        source_image=image_path,
        layout=layout,
        palette=palette,
        circles=circles,
    )


def export_project(project: Project, config: AppConfig) -> dict[str, Path]:
    """Export the Version 0.3 artifact set."""
    output_folder = config.output_folder
    paths = {
        "svg": output_folder / "coloring_page.svg",
        "numbered_preview_png": output_folder / "preview_numbered.png",
        "preview_png": output_folder / "preview.png",
        "colored_preview_png": output_folder / "preview_colored.png",
        "answer_png": output_folder / "answer_page.png",
        "legend_png": output_folder / "color_legend.png",
        "coloring_page_pdf": output_folder / "coloring_page.pdf",
        "answer_pdf": output_folder / "answer_page.pdf",
        "legend_pdf": output_folder / "color_legend.pdf",
        "project_json": output_folder / "project.json",
    }
    SvgExporter().export(project.circles, project.layout, paths["svg"])
    preview_exporter = PreviewExporter()
    preview_exporter.export_numbered(project.circles, project.layout, paths["numbered_preview_png"])
    preview_exporter.export_colored(project.circles, project.layout, paths["preview_png"])
    preview_exporter.export_colored(project.circles, project.layout, paths["colored_preview_png"])
    AnswerExporter().export(project.circles, project.layout, paths["answer_png"])
    LegendExporter().export(project.palette, paths["legend_png"])
    pdf_exporter = PdfExporter()
    pdf_exporter.export_image(paths["numbered_preview_png"], paths["coloring_page_pdf"])
    pdf_exporter.export_image(paths["answer_png"], paths["answer_pdf"])
    pdf_exporter.export_image(paths["legend_png"], paths["legend_pdf"])
    ProjectExporter().export(project, paths["project_json"])
    return paths


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="Generate mosaic coloring page assets.")
    parser.add_argument("--input", type=Path, help="Input artwork path.")
    parser.add_argument("--output", type=Path, help="Output folder.")
    parser.add_argument("--colors", type=int, help="Number of colors to preserve.")
    parser.add_argument("--circle-diameter", type=float, help="Circle diameter in millimetres.")
    parser.add_argument("--circle-gap", type=float, help="Gap between circles in millimetres.")
    parser.add_argument("--page-width", type=float, help="Custom page width in millimetres.")
    parser.add_argument("--page-height", type=float, help="Custom page height in millimetres.")
    parser.add_argument("--orientation", choices=("portrait", "landscape"), help="Page orientation.")
    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> AppConfig:
    """Create application config from CLI overrides."""
    defaults = AppConfig()
    mosaic = MosaicSettings(
        circle_diameter_mm=args.circle_diameter or defaults.mosaic.circle_diameter_mm,
        circle_gap_mm=args.circle_gap if args.circle_gap is not None else defaults.mosaic.circle_gap_mm,
        number_of_colors=args.colors or defaults.mosaic.number_of_colors,
    )
    page = PageSettings(
        name="Custom" if args.page_width or args.page_height else defaults.page.name,
        width_mm=args.page_width or defaults.page.width_mm,
        height_mm=args.page_height or defaults.page.height_mm,
        orientation=args.orientation or defaults.page.orientation,
        margins=defaults.page.margins,
    )
    return AppConfig(
        page=page,
        mosaic=mosaic,
        image_processing=defaults.image_processing,
        input_folder=defaults.input_folder,
        output_folder=args.output or defaults.output_folder,
        default_input_name=defaults.default_input_name,
        project_name=defaults.project_name,
    )


def main() -> int:
    """Run MosaicGenerator."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    config = config_from_args(args)
    image_path = args.input or config.default_input_path
    try:
        project = build_project(config, image_path)
        paths = export_project(project, config)
    except Exception:
        LOGGER.exception("Mosaic generation failed")
        return 1
    print("MosaicGenerator Version 0.3 completed")
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
