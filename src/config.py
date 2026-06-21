"""Application configuration for MosaicGenerator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final


ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Margins:
    """Printable page margins in millimetres."""

    top_mm: float = 15.0
    bottom_mm: float = 15.0
    left_mm: float = 15.0
    right_mm: float = 15.0


@dataclass(frozen=True)
class PageSettings:
    """Page setup for print-ready output."""

    name: str = "A4"
    width_mm: float = 210.0
    height_mm: float = 297.0
    orientation: str = "portrait"
    margins: Margins = field(default_factory=Margins)

    def normalized(self) -> "PageSettings":
        """Return page settings with dimensions matching the orientation."""
        orientation = self.orientation.lower()
        if orientation not in {"portrait", "landscape"}:
            raise ValueError("orientation must be 'portrait' or 'landscape'")
        width, height = self.width_mm, self.height_mm
        if orientation == "portrait" and width > height:
            width, height = height, width
        if orientation == "landscape" and height > width:
            width, height = height, width
        return PageSettings(self.name, width, height, orientation, self.margins)


@dataclass(frozen=True)
class MosaicSettings:
    """Dot and palette controls for mosaic generation."""

    circle_diameter_mm: float = 3.5
    circle_gap_mm: float = 0.3
    number_of_colors: int = 12
    background_rgb: tuple[int, int, int] = (255, 255, 255)
    stroke_rgb: tuple[int, int, int] = (25, 25, 25)

    @property
    def pitch_mm(self) -> float:
        """Distance between circle centres."""
        return self.circle_diameter_mm + self.circle_gap_mm


@dataclass(frozen=True)
class ImageProcessingSettings:
    """Controls for image preparation before color reduction."""

    auto_brightness: bool = True
    auto_contrast: bool = True
    edge_preservation: bool = True
    sharpen: bool = True
    denoise: bool = True


@dataclass(frozen=True)
class AppConfig:
    """Top-level configuration used by the end-to-end pipeline."""

    page: PageSettings = field(default_factory=PageSettings)
    mosaic: MosaicSettings = field(default_factory=MosaicSettings)
    image_processing: ImageProcessingSettings = field(default_factory=ImageProcessingSettings)
    input_folder: Path = ROOT_DIR / "input_images"
    output_folder: Path = ROOT_DIR / "output"
    default_input_name: str = "sample.jpg"
    project_name: str = "mosaic_project"

    @property
    def default_input_path(self) -> Path:
        """Default image path for command-line runs."""
        return self.input_folder / self.default_input_name
