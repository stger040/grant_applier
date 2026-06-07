"""Profile state helpers for opportunity workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .analyzer import analyze_opportunity
from .discovery import Opportunity


def profile_json_path(opportunity: Opportunity) -> Path:
    return opportunity.path / "Analysis" / "opportunity_profile.json"


def save_profile_json(opportunity: Opportunity, profile: dict[str, Any]) -> None:
    path = profile_json_path(opportunity)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def load_profile_json(opportunity: Opportunity) -> dict[str, Any] | None:
    path = profile_json_path(opportunity)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_profile(opportunity: Opportunity, overwrite: bool = False) -> dict[str, Any]:
    if overwrite:
        profile = analyze_opportunity(opportunity, overwrite=True)
        save_profile_json(opportunity, profile)
        return profile
    existing = load_profile_json(opportunity)
    if existing is not None:
        return existing
    profile = analyze_opportunity(opportunity, overwrite=False)
    save_profile_json(opportunity, profile)
    return profile
