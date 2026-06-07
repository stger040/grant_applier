"""Opportunity profile generation and scaffold output writers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .discovery import Opportunity, list_local_source_files


@dataclass(frozen=True)
class SourceSignals:
    local_grants_gov_notice_found: bool
    full_nofo_found: bool
    official_funder_page_found: bool = False


def analyze_opportunity(opportunity: Opportunity, overwrite: bool = False) -> dict[str, Any]:
    """Build profile data and write scaffold outputs for one opportunity."""
    local_sources = list_local_source_files(opportunity.path)
    local_rel_paths = [str(path.relative_to(opportunity.path)) for path in local_sources]
    funder = infer_funder(opportunity.opportunity_folder, local_rel_paths)
    opportunity_number = infer_opportunity_number(opportunity.opportunity_folder, funder)
    signals = detect_source_signals(local_rel_paths, funder, opportunity_number)

    profile: dict[str, Any] = {
        "applicant_folder": opportunity.applicant_folder,
        "opportunity_folder": opportunity.opportunity_folder,
        "likely_applicant": infer_likely_applicant(opportunity.applicant_folder),
        "opportunity_number": opportunity_number,
        "opportunity_title": "[CONFIRM]",
        "funder": funder,
        "submission_system": infer_submission_system(funder),
        "deadline": "[CONFIRM]",
        "award_ceiling": "[CONFIRM]",
        "project_period": "[CONFIRM]",
        "eligibility": {
            "sgdi_eligible": "[CONFIRM]" if opportunity.applicant_folder == "SGDI" else "N/A",
            "notes": ["[TODO] Verify applicant eligibility from official funder guidance."],
        },
        "cost_share_required": "[CONFIRM]",
        "indirect_cost_rules": "[CONFIRM]",
        "source_status": {
            "local_grants_gov_notice_found": signals.local_grants_gov_notice_found,
            "full_nofo_found": signals.full_nofo_found,
            "official_funder_page_found": signals.official_funder_page_found,
        },
        "known_local_source_documents": local_rel_paths,
        "human_review_required": True,
    }

    write_scaffold_outputs(
        opportunity=opportunity,
        profile=profile,
        local_relative_paths=local_rel_paths,
        signals=signals,
        overwrite=overwrite,
    )
    profile_json_path = opportunity.path / "Analysis" / "opportunity_profile.json"
    write_if_allowed(profile_json_path, json.dumps(profile, indent=2), overwrite=overwrite)
    return profile


def infer_likely_applicant(applicant_folder: str) -> str:
    if applicant_folder == "SGDI":
        return "St Germaine Data Innovations (SGDI)"
    if applicant_folder == "AAIP":
        return "American Association of Indian Physicians (AAIP)"
    if applicant_folder == "LCOOU":
        return "Lac Courte Oreilles Ojibwe University (LCOOU)"
    return applicant_folder


def infer_funder(opportunity_name: str, local_relative_paths: list[str]) -> str:
    haystack = " ".join([opportunity_name, *local_relative_paths]).lower()
    keyword_map = {
        "National Science Foundation": ("nsf",),
        "Department of Education": ("ed-grant", "department of education"),
        "USDA NIFA": ("usda-nifa", "nifa"),
        "Department of Justice / National Institute of Justice": ("o-nij", "nij", "ojp"),
        "HHS / ACL / NIDILRR": ("hhs", "acl", "nidilrr"),
        "Department of State": ("dfop", "state.gov", "embassy"),
    }
    for funder, keywords in keyword_map.items():
        if any(keyword in haystack for keyword in keywords):
            return funder
    return "[CONFIRM]"


def infer_opportunity_number(opportunity_name: str, funder: str) -> str:
    trimmed = opportunity_name.strip()
    if re.fullmatch(r"\d{2}-\d{3}", trimmed) and "National Science Foundation" in funder:
        return f"NSF {trimmed}"
    return trimmed


def infer_submission_system(funder: str) -> str:
    if funder == "National Science Foundation":
        return "Research.gov + Grants.gov"
    if funder == "[CONFIRM]":
        return "[CONFIRM]"
    return "Grants.gov"


def detect_source_signals(
    local_relative_paths: list[str], funder: str, opportunity_number: str
) -> SourceSignals:
    lowercase_paths = [path.lower() for path in local_relative_paths]
    local_grants_gov_notice = any(
        "grants.gov" in path or "search results detail" in path for path in lowercase_paths
    )
    nofo_keywords = (
        "nofo",
        "solicitation",
        "notice of funding opportunity",
        "request for applications",
        "rfa",
        "funding opportunity announcement",
        "proposal requirement",
        "application instructions",
    )
    full_nofo_found = any(any(keyword in path for keyword in nofo_keywords) for path in lowercase_paths)
    if not full_nofo_found and funder == "National Science Foundation":
        nsf_number = opportunity_number.replace("NSF", "").strip().lower()
        full_nofo_found = any("nsf" in path and nsf_number in path for path in lowercase_paths)
    return SourceSignals(
        local_grants_gov_notice_found=local_grants_gov_notice,
        full_nofo_found=full_nofo_found,
    )


def write_scaffold_outputs(
    opportunity: Opportunity,
    profile: dict[str, Any],
    local_relative_paths: list[str],
    signals: SourceSignals,
    overwrite: bool,
) -> None:
    analysis_dir = opportunity.path / "Analysis"
    sources_dir = opportunity.path / "Sources"
    compliance_dir = opportunity.path / "Compliance"
    drafts_dir = opportunity.path / "Drafts"
    budgets_dir = opportunity.path / "Budgets"

    write_if_allowed(
        analysis_dir / "opportunity_profile.yaml",
        render_yaml(profile),
        overwrite=overwrite,
    )
    write_if_allowed(
        analysis_dir / "required_documents.md",
        required_documents_template(signals),
        overwrite=overwrite,
    )
    write_if_allowed(
        analysis_dir / "eligibility_assessment.md",
        eligibility_assessment_template(opportunity),
        overwrite=overwrite,
    )
    write_if_allowed(
        analysis_dir / "review_criteria.md",
        review_criteria_template(),
        overwrite=overwrite,
    )
    write_if_allowed(
        analysis_dir / "compliance_checklist.md",
        compliance_checklist_template(),
        overwrite=overwrite,
    )
    write_if_allowed(
        analysis_dir / "drafting_strategy.md",
        drafting_strategy_template(opportunity),
        overwrite=overwrite,
    )
    write_if_allowed(
        analysis_dir / "human_review_todo.md",
        human_review_todo_template(signals),
        overwrite=overwrite,
    )
    write_if_allowed(
        sources_dir / "source_index.md",
        source_index_template(local_relative_paths, signals),
        overwrite=overwrite,
    )
    write_if_allowed(
        sources_dir / "sources.json",
        build_sources_json(local_relative_paths),
        overwrite=overwrite,
    )
    write_if_allowed(
        compliance_dir / "final_submission_checklist.md",
        final_submission_checklist_template(),
        overwrite=overwrite,
    )
    drafts_dir.mkdir(parents=True, exist_ok=True)
    budgets_dir.mkdir(parents=True, exist_ok=True)


def write_if_allowed(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def build_sources_json(local_relative_paths: list[str]) -> str:
    payload: list[dict[str, Any]] = []
    today = date.today().isoformat()
    for relative_path in local_relative_paths:
        payload.append(
            {
                "title": Path(relative_path).name,
                "url": None,
                "local_path": relative_path,
                "source_type": "local_source",
                "retrieved_date": today,
                "notes": "Local folder source. Official source verification still required.",
            }
        )
    return json.dumps(payload, indent=2)


def required_documents_template(signals: SourceSignals) -> str:
    return f"""# Required Documents (Initial Skeleton)

Status: Not yet complete. Official funder requirements must be confirmed from authoritative sources.

## Source Validation Status

- Local Grants.gov notice found: `{signals.local_grants_gov_notice_found}`
- Full local NOFO/solicitation detected: `{signals.full_nofo_found}`
- Official funder web page verified: `{signals.official_funder_page_found}`

## Required Documents

- [TODO] Extract required narrative sections from official NOFO/solicitation.
- [TODO] Extract page limits and formatting rules with source citations.
- [TODO] Extract required forms, attachments, and certifications.
- [TODO] Add explicit source URL/file citation for every major requirement.
"""


def eligibility_assessment_template(opportunity: Opportunity) -> str:
    return f"""# Eligibility Assessment (Initial Skeleton)

Opportunity: `{opportunity.relative_id}`

- Applicant folder context: `{opportunity.applicant_folder}`
- Direct eligibility confirmed from official source: `[CONFIRM]`
- Eligibility risks identified: `[TODO]`

## Required Follow-Up

1. [TODO] Confirm eligible applicant types from official funder notice.
2. [TODO] Confirm whether the likely applicant can submit as prime.
3. [TODO] If ineligible, identify recommended eligible prime partner.
"""


def review_criteria_template() -> str:
    return """# Review Criteria (Initial Skeleton)

- [TODO] Extract and list official merit/review criteria with source citations.
- [TODO] Document scoring structure, if published.
- [TODO] Note any threshold requirements, priorities, or tie-breakers.
"""


def compliance_checklist_template() -> str:
    return """# Compliance Checklist (Initial Skeleton)

- [ ] [TODO] Confirm registration requirements (SAM/UEI/Grants.gov/agency portal).
- [ ] [TODO] Confirm all mandatory forms and attachments.
- [ ] [TODO] Confirm page limits and formatting constraints.
- [ ] [TODO] Confirm budget rules (allowable costs, indirect limits, match).
- [ ] [TODO] Confirm submission deadline and time zone.
"""


def drafting_strategy_template(opportunity: Opportunity) -> str:
    return f"""# Drafting Strategy (Initial Skeleton)

Opportunity: `{opportunity.relative_id}`

- [TODO] Align document structure to the official funder section headings.
- [TODO] Identify required partner roles and narrative themes.
- [TODO] Define missing factual inputs that block full draft completion.
"""


def human_review_todo_template(signals: SourceSignals) -> str:
    missing_nofo = "Yes" if not signals.full_nofo_found else "No"
    return f"""# Human Review TODO

- [ ] Confirm official funder NOFO/solicitation source URL and archived copy.
- [ ] Confirm deadline, award ceiling, and project period from official source.
- [ ] Confirm eligibility and applicant type requirements.
- [ ] Confirm cost share/match requirement and indirect cost restrictions.
- [ ] Confirm required forms, attachments, and submission portal rules.
- [ ] Confirm page limits and formatting requirements for every narrative.

## Flags

- Local full NOFO appears missing: `{missing_nofo}`
- Official funder web source verified: `{signals.official_funder_page_found}`
"""


def source_index_template(local_relative_paths: list[str], signals: SourceSignals) -> str:
    local_items = "\n".join(f"- `{path}`" for path in local_relative_paths) or "- [TODO] No local files found."
    return f"""# Source Index

## Local Sources

{local_items}

## Official Source Discovery Status

- Local Grants.gov detail found: `{signals.local_grants_gov_notice_found}`
- Full NOFO/solicitation found locally: `{signals.full_nofo_found}`
- Official funder page verified online: `{signals.official_funder_page_found}`

## Required Next Steps

1. [TODO] Locate official funder NOFO/solicitation page.
2. [TODO] Add official source URLs and retrieval dates.
3. [TODO] Link each major requirement to an authoritative source.
"""


def final_submission_checklist_template() -> str:
    return """# Final Submission Checklist (Initial Skeleton)

Status: `draft_not_submission_ready`

- [ ] Authorized representative confirmed.
- [ ] Eligibility confirmed.
- [ ] Final budget and indirect rate confirmed.
- [ ] All required forms completed.
- [ ] All required attachments complete.
- [ ] Page limit and format checks passed.
- [ ] Deadline and submission portal confirmed.
"""


def render_yaml(value: Any, indent: int = 0) -> str:
    """Render Python values to a deterministic YAML string."""
    lines = _render_yaml_lines(value, indent=indent)
    return "\n".join(lines)


def _render_yaml_lines(value: Any, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, child in value.items():
            if isinstance(child, dict):
                if child:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_render_yaml_lines(child, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {{}}")
            elif isinstance(child, list):
                if child:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_render_yaml_lines(child, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: []")
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(child)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_render_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_yaml_scalar(value)}"]


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    return str(value)
