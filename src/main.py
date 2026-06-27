"""Command-line entry point for MosaicGenerator."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import (AppConfig, ImageProcessingSettings, MosaicSettings,
                        PAGE_PRESETS, PageSettings)
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
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class PipelineResult:
    project: Project
    original_preview: Image.Image
    quantized_preview: Image.Image


def build_pipeline(config: AppConfig, image_path: Path) -> PipelineResult:
    layout = LayoutEngine(config.page, config.mosaic).calculate()
    image_engine = ImageEngine(config.image_processing)
    source_image = image_engine.load(image_path)
    optimized_image = image_engine.optimize(source_image)
    quality_image = image_engine.resize_for_quality_grid(optimized_image, layout)
    edge_map = image_engine.edge_map(quality_image)
    candidates = image_engine.sample_candidates_for_layout(quality_image, layout, edge_map)

    palette_engine = PaletteEngine(
        config.mosaic.number_of_colors,
        config.image_processing,
        config.mosaic.white_threshold,
        config.mosaic.dark_background_threshold,
    )

    best_grid = best_mapped = best_palette = None
    best_score = float("inf")
    for candidate in candidates:
        mapped, palette = palette_engine.reduce(candidate, edge_map)
        score = image_engine.score_grid(mapped, quality_image, edge_map)
        if score < best_score:
            best_score, best_grid, best_mapped, best_palette = score, candidate, mapped, palette

    if best_mapped is None or best_palette is None or best_grid is None:
        raise RuntimeError("No mosaic candidates were generated.")

    circles = MosaicEngine().create_circles(
        best_mapped, layout, best_palette,
        config.mosaic.dark_background_threshold)
    project = Project(config.project_name, image_path, layout, best_palette, circles)
    LOGGER.info("Selected candidate score: %.3f", best_score)
    return PipelineResult(
        project,
        best_grid.resize(quality_image.size, Image.Resampling.NEAREST),
        best_mapped.resize(quality_image.size, Image.Resampling.NEAREST),
    )


def build_project(config: AppConfig, image_path: Path) -> Project:
    return build_pipeline(config, image_path).project


def export_project(result: PipelineResult, config: AppConfig) -> dict[str, Path]:
    project = result.project
    out = config.output_folder
    paths = {
        "svg":                  out / "coloring_page.svg",
        "numbered_preview_png": out / "preview_numbered.png",
        "preview_png":          out / "preview.png",
        "colored_preview_png":  out / "preview_colored.png",
        "original_preview_png": out / "original_preview.png",
        "quantized_preview_png":out / "quantized_preview.png",
        "answer_png":           out / "answer_page.png",
        "legend_png":           out / "color_legend.png",
        "coloring_page_pdf":    out / "coloring_page.pdf",
        "answer_pdf":           out / "answer_page.pdf",
        "legend_pdf":           out / "color_legend.pdf",
        "legend_page_pdf":      out / "legend_page.pdf",
        "project_json":         out / "project.json",
    }
    bg      = config.mosaic.resolved_background_rgb
    outline = config.mosaic.resolved_circle_outline_rgb
    number  = config.mosaic.resolved_number_rgb
    answer_bg = config.mosaic.answer_background_color

    SvgExporter().export(project.circles, project.layout, paths["svg"], bg, outline, number)
    preview = PreviewExporter()
    preview.export_numbered(project.circles, project.layout, paths["numbered_preview_png"],
                            background_rgb=bg, circle_outline_rgb=outline, number_rgb=number)
    preview.export_colored(project.circles, project.layout, paths["preview_png"], background_rgb=answer_bg)
    preview.export_colored(project.circles, project.layout, paths["colored_preview_png"], background_rgb=answer_bg)
    preview.export_image_preview(result.original_preview, paths["original_preview_png"])
    preview.export_image_preview(result.quantized_preview, paths["quantized_preview_png"])
    AnswerExporter().export(project.circles, project.layout, paths["answer_png"], background_rgb=answer_bg)
    LegendExporter().export(project.palette, paths["legend_png"])
    pdf = PdfExporter()
    pdf.export_image(paths["numbered_preview_png"], paths["coloring_page_pdf"])
    pdf.export_image(paths["answer_png"],           paths["answer_pdf"])
    pdf.export_image(paths["legend_png"],           paths["legend_pdf"])
    pdf.export_image(paths["legend_png"],           paths["legend_page_pdf"])
    ProjectExporter().export(project, paths["project_json"])
    return paths


def run_single(config: AppConfig, image_path: Path,
               output_folder: Path | None = None) -> dict[str, Path]:
    output_config = replace(config,
        output_folder=output_folder or config.output_folder,
        project_name=_safe_name(image_path))
    return export_project(build_pipeline(output_config, image_path), output_config)


def run_batch(config: AppConfig, input_folder: Path,
              output_root: Path) -> list[tuple[Path, dict[str, Path]]]:
    image_paths = sorted(p for p in input_folder.iterdir()
                         if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    if not image_paths:
        raise FileNotFoundError(f"No supported images in {input_folder}")
    return [(p, run_single(config, p, output_root / _safe_name(p)))
            for p in image_paths]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate mosaic coloring page assets.")
    parser.add_argument("--input",  type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--batch",  action="store_true")
    parser.add_argument("--page-size", choices=tuple(PAGE_PRESETS.keys()), default="A4")
    parser.add_argument("--quality", choices=("LOW","MEDIUM","HIGH","ULTRA"), default="ULTRA")
    parser.add_argument("--colors", type=int)
    parser.add_argument("--circle-diameter", type=float)
    parser.add_argument("--circle-gap", type=float)
    parser.add_argument("--page-width", type=float)
    parser.add_argument("--page-height", type=float)
    parser.add_argument("--orientation", choices=("portrait","landscape"))
    parser.add_argument("--dark-theme", action="store_true")
    parser.add_argument(
        "--keep-bg", action="store_true",
        help=(
            "Do NOT crop the background. Render it as coloured dots instead. "
            "Use this when the background is part of the design "
            "(e.g. dog on purple bg, character on coloured scene)."
        ),
    )
    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> AppConfig:
    defaults = AppConfig()
    page = _page_from_args(args, defaults)
    keep_bg = bool(getattr(args, "keep_bg", False))
    mosaic = MosaicSettings(
        circle_diameter_mm=args.circle_diameter or defaults.mosaic.circle_diameter_mm,
        circle_gap_mm=(args.circle_gap if args.circle_gap is not None
                       else defaults.mosaic.circle_gap_mm),
        number_of_colors=min(25, args.colors or defaults.mosaic.number_of_colors),
        white_threshold=defaults.mosaic.white_threshold,
        dark_background_threshold=defaults.mosaic.dark_background_threshold,
        background_color=defaults.mosaic.background_color,
        circle_outline_color=defaults.mosaic.circle_outline_color,
        number_color=defaults.mosaic.number_color,
        dark_theme=args.dark_theme or defaults.mosaic.dark_theme,
        answer_background_color=defaults.mosaic.answer_background_color,
        keep_background=keep_bg,
    )
    image_processing = ImageProcessingSettings(
        quality=args.quality,
        keep_background=keep_bg,
    )
    return AppConfig(page, mosaic, image_processing,
                     defaults.input_folder,
                     args.output or defaults.output_folder,
                     defaults.default_input_name,
                     defaults.project_name)


def _page_from_args(args, defaults):
    orientation = args.orientation or defaults.page.orientation
    if args.page_width or args.page_height:
        return PageSettings("Custom",
            args.page_width or defaults.page.width_mm,
            args.page_height or defaults.page.height_mm,
            orientation, defaults.page.margins).normalized()
    return PageSettings.from_preset(args.page_size, orientation, defaults.page.margins)


def _safe_name(p: Path) -> str:
    return (re.sub(r"[^A-Za-z0-9_-]+", "_", p.stem.strip() or "mosaic")
            .strip("_") or "mosaic")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    config = config_from_args(args)
    try:
        if args.batch:
            input_folder = (args.input if args.input and args.input.is_dir()
                            else config.input_folder)
            results = run_batch(config, input_folder,
                                args.output or config.output_folder)
            print("Batch completed")
            for p, paths in results:
                print(f"  {p.name}: {paths['project_json'].parent}")
        else:
            paths = run_single(config,
                               args.input or config.default_input_path,
                               args.output)
            print("MosaicGenerator completed")
            for label, path in paths.items():
                print(f"  {label}: {path}")
    except Exception:
        LOGGER.exception("Generation failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
