"""Load campaign templates from the templates/ directory.

Templates are YAML files defining a task DAG + LS XML configs per task.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

if "TEMPLATES_DIR" in os.environ:
    TEMPLATES_DIR = Path(os.environ["TEMPLATES_DIR"])
else:
    TEMPLATES_DIR = Path(__file__).resolve().parents[4] / "templates"


def load_template(template_id: str) -> dict[str, Any]:
    """Load and parse a campaign template by ID.

    Returns the parsed YAML with annotation_config XML strings
    injected into each task entry.
    """
    template_dir = TEMPLATES_DIR / template_id
    campaign_file = template_dir / "campaign.yaml"
    if not campaign_file.exists():
        raise FileNotFoundError(f"Template not found: {template_id}")

    with open(campaign_file) as f:
        template = yaml.safe_load(f)

    # Inject XML annotation configs into task definitions
    for task in template.get("tasks", []):
        xml_file = task.pop("annotation_config_file", None)
        if xml_file:
            xml_path = template_dir / xml_file
            if xml_path.exists():
                task["annotation_config"] = xml_path.read_text()
            else:
                task["annotation_config"] = None

    return template


def list_templates() -> list[str]:
    """Return IDs of all available templates."""
    if not TEMPLATES_DIR.exists():
        return []
    return [
        d.name
        for d in TEMPLATES_DIR.iterdir()
        if d.is_dir() and (d / "campaign.yaml").exists()
    ]
