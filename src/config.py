"""Application configuration for MosaicGenerator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal


ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
RgbColor = tuple[int, int, int]
QualityPreset = Literal["LOW", "MEDIUM", "HIGH", "ULTRA"]

PAGE_PRESETS: Final[dict[str, tuple[float, float]]] = {
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
}


@dataclass(frozen=True)
class Margins:
    top_mm: float = 10.0
    bottom_mm: float = 10.0
    left_mm: float = 10.0
    right_mm: float = 10.0


@dataclass(frozen=True)
class PageSettings:
    name: str = "A4"
    width_mm: float = 210.0
    height_mm: float = 297.0
    orientation: str = "portrait"
    margins: Margins = field(default_factory=Margins)

    @classmethod
    def from_preset(cls, page_size: str, orientation: str = "portrait",
                    margins: Margins | None = None) -> "PageSettings":
        normalized_size = page_size.upper()
        if normalized_size not in PAGE_PRESETS:
            raise ValueError(f"Unsupported page size: {page_size}")
        width, height = PAGE_PRESETS[normalized_size]
        return cls(normalized_size, width, height, orientation,
                   margins or Margins()).normalized()

    def normalized(self) -> "PageSettings":
        orientation = self.orientation.lower()
        if orientation not in {"portrait", "landscape"}:
            raise ValueError("orientation must be 'portrait' or 'landscape'")
        width, height = self.width_mm, self.height_mm
        if orientation == "portrait" and width > height:
            width, height = height, width
        if orientation == "landscape" and height > width:
            width, height = height, width
        return PageSettings(self.name.upper(), width, height, orientation,
                            self.margins)


@dataclass(frozen=True)
class MosaicSettings:
    circle_diameter_mm: float = 3.5
    circle_gap_mm: float = 0.25
    number_of_colors: int = 25
    white_threshold: int = 245
    # Near-black pixels darker than this are treated as "black background"
    # and rendered as BLACK FILLED dots (pen 0) on the answer page.
    # Set to 0 to disable black-background suppression entirely.
    dark_background_threshold: int = 28
    background_color: RgbColor = (0, 0, 0)
    circle_outline_color: RgbColor = (255, 255, 255)
    number_color: RgbColor = (0, 0, 0)
    dark_theme: bool = True
    answer_background_color: RgbColor = (0, 0, 0)
    # When True: do NOT crop background — render it as colored dots.
    # Use --keep-bg on the CLI to set this.
    keep_background: bool = False

    @property
    def pitch_mm(self) -> float:
        return self.circle_diameter_mm + self.circle_gap_mm

    @property
    def resolved_background_rgb(self) -> RgbColor:
        return (0, 0, 0) if self.dark_theme else self.background_color

    @property
    def resolved_circle_outline_rgb(self) -> RgbColor:
        return (255, 255, 255) if self.dark_theme else self.circle_outline_color

    @property
    def resolved_number_rgb(self) -> RgbColor:
        return self.number_color


@dataclass(frozen=True)
class ImageProcessingSettings:
    quality: QualityPreset = "ULTRA"
    auto_contrast: bool = True
    contrast_cutoff_percent: float = 0.5
    bilateral_filter: bool = True
    edge_preservation: bool = True
    adaptive_sharpen: bool = True
    high_resolution_scale: int = 7
    max_processing_edge_px: int = 2400
    dithering_strength: float = 0.0
    candidate_count: int = 4
    saturation_boost: float = 1.55
    # Subject-fill zoom: crop away uniform backgrounds
    subject_fill_zoom: bool = True
    # When True: skip background crop entirely (--keep-bg mode)
    keep_background: bool = False
    background_luma_threshold: int = 30

    def tuned(self) -> "ImageProcessingSettings":
        presets = {
            "LOW":    dict(high_resolution_scale=3, candidate_count=1),
            "MEDIUM": dict(high_resolution_scale=4, candidate_count=2),
            "HIGH":   dict(high_resolution_scale=5, candidate_count=3),
            "ULTRA":  dict(high_resolution_scale=7, candidate_count=4),
        }
        return ImageProcessingSettings(
            **{**self.__dict__, **presets[self.quality]})


@dataclass(frozen=True)
class AppConfig:
    page: PageSettings = field(default_factory=PageSettings)
    mosaic: MosaicSettings = field(default_factory=MosaicSettings)
    image_processing: ImageProcessingSettings = field(
        default_factory=ImageProcessingSettings)
    input_folder: Path = ROOT_DIR / "input_images"
    output_folder: Path = ROOT_DIR / "output"
    default_input_name: str = "sample.jpg"
    project_name: str = "mosaic_project"

    @property
    def default_input_path(self) -> Path:
        for candidate in (self.input_folder / self.default_input_name,
                          self.input_folder / "Sample.jpg"):
            if candidate.exists():
                return candidate
        return self.input_folder / self.default_input_name
