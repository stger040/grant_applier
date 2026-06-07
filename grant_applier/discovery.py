"""Opportunity discovery and local source inventory helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

APPLICANT_FOLDERS = ("AAIP", "SGDI", "LCOOU")
GENERATED_FOLDERS = {"Analysis", "Sources", "Compliance", "Budgets"}


@dataclass(frozen=True)
class Opportunity:
    """Represents a grant opportunity folder in the repository."""

    applicant_folder: str
    opportunity_folder: str
    path: Path

    @property
    def relative_id(self) -> str:
        return f"{self.applicant_folder}/{self.opportunity_folder}"


def discover_opportunities(root: Path) -> list[Opportunity]:
    """Find all first-level opportunity directories under applicant folders."""
    opportunities: list[Opportunity] = []
    for applicant in APPLICANT_FOLDERS:
        applicant_dir = root / applicant
        if not applicant_dir.is_dir():
            continue
        for entry in sorted(applicant_dir.iterdir(), key=lambda item: item.name.lower()):
            if entry.is_dir():
                opportunities.append(
                    Opportunity(
                        applicant_folder=applicant,
                        opportunity_folder=entry.name,
                        path=entry,
                    )
                )
    return opportunities


def list_local_source_files(opportunity_dir: Path) -> list[Path]:
    """Return local source files while ignoring generated output folders."""
    files: list[Path] = []
    for path in opportunity_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        relative = path.relative_to(opportunity_dir)
        if any(part in GENERATED_FOLDERS for part in relative.parts):
            continue
        files.append(path)
    return sorted(files, key=lambda item: str(item).lower())
