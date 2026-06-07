"""Inventory command implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .discovery import Opportunity, discover_opportunities, list_local_source_files


def build_inventory(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for opportunity in discover_opportunities(root):
        local_file_count = len(list_local_source_files(opportunity.path))
        rows.append(
            {
                "opportunity": opportunity.relative_id,
                "applicant_folder": opportunity.applicant_folder,
                "opportunity_folder": opportunity.opportunity_folder,
                "local_file_count": local_file_count,
                "profile_exists": (opportunity.path / "Analysis" / "opportunity_profile.yaml").exists(),
            }
        )
    return rows


def inventory_text_table(items: list[dict[str, Any]]) -> str:
    headers = ("opportunity", "local_files", "profile_exists")
    rows = [
        (item["opportunity"], str(item["local_file_count"]), str(item["profile_exists"]))
        for item in items
    ]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def format_row(values: tuple[str, str, str]) -> str:
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(values))

    divider = "-+-".join("-" * width for width in widths)
    output_lines = [format_row(headers), divider]
    output_lines.extend(format_row(row) for row in rows)
    return "\n".join(output_lines)


def inventory_json(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, indent=2)


def resolve_opportunity(root: Path, opportunity_id: str) -> Opportunity:
    normalized = opportunity_id.strip().replace("\\", "/")
    for opportunity in discover_opportunities(root):
        if opportunity.relative_id == normalized:
            return opportunity
    raise ValueError(f"Opportunity not found: {opportunity_id}")
