"""Project model and serialization helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.models.circle import Circle
from src.models.page import Layout
from src.models.palette import Palette


@dataclass(frozen=True, slots=True)
class Project:
    """Complete data required to regenerate current Version 0.3 exports."""

    name: str
    source_image: Path
    layout: Layout
    palette: Palette
    circles: tuple[Circle, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the project to JSON-compatible primitives."""
        data = asdict(self)
        data["source_image"] = str(self.source_image)
        return data
