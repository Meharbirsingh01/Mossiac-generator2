"""Project JSON exporter."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.models.project import Project

LOGGER = logging.getLogger(__name__)


class ProjectExporter:
    """Persist project data for future reload support."""

    def export(self, project: Project, output_path: Path) -> Path:
        """Write a JSON project file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")
        LOGGER.info("Wrote project JSON: %s", output_path)
        return output_path
