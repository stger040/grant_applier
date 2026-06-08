"""Draft generation for opportunity narrative packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .discovery import Opportunity
from .llm import generate_section_with_openai
from .profiles import ensure_profile


def generate_drafts(
    opportunity: Opportunity,
    overwrite: bool = False,
    use_llm: bool = False,
    llm_model: str = "gpt-4.1-mini",
) -> list[Path]:
    profile = ensure_profile(opportunity, overwrite=False)
    requirements = load_requirements(opportunity)
    readiness = load_readiness(opportunity)
    drafts_dir = opportunity.path / "Drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    sections = section_plan_for_funder(str(profile.get("funder", "[CONFIRM]")))
    sections = merge_sections_with_readiness(sections, readiness)
    expected_names = {f"{idx:02d}_{slugify(section)}.md" for idx, section in enumerate(sections, start=1)}
    if overwrite:
        for existing in drafts_dir.glob("[0-9][0-9]_*.md"):
            if existing.name not in expected_names:
                existing.unlink()

    created: list[Path] = []
    for index, section in enumerate(sections, start=1):
        filename = f"{index:02d}_{slugify(section)}.md"
        path = drafts_dir / filename
        if path.exists() and not overwrite:
            continue
        readiness_item = resolve_readiness_for_section(section, readiness)
        mode = drafting_mode_from_readiness(readiness_item)
        path.write_text(
            render_draft_section(
                section_name=section,
                profile=profile,
                requirements=requirements,
                opportunity=opportunity,
                readiness_item=readiness_item,
                mode=mode,
                use_llm=use_llm,
                llm_model=llm_model,
            ).rstrip()
            + "\n",
            encoding="utf-8",
        )
        created.append(path)
    return created


def load_requirements(opportunity: Opportunity) -> dict[str, Any]:
    path = opportunity.path / "Analysis" / "requirements.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        return {}
    return {}


def load_readiness(opportunity: Opportunity) -> dict[str, Any]:
    path = opportunity.path / "Analysis" / "document_readiness.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        return {}
    return {}


def merge_sections_with_readiness(
    sections: list[str],
    readiness: dict[str, Any],
) -> list[str]:
    merged = list(sections)
    seen = {normalize_name(section) for section in merged}
    for item in readiness.get("documents", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        normalized = normalize_name(name)
        if normalized in seen:
            continue
        merged.append(name)
        seen.add(normalized)
    return merged


def section_plan_for_funder(funder: str) -> list[str]:
    plans = {
        "National Science Foundation": [
            "Project Summary",
            "Project Description",
            "Budget Justification",
            "Data Management and Sharing Plan",
            "Facilities, Equipment, and Other Resources",
            "References Cited",
        ],
        "HHS / ACL / NIDILRR": [
            "Project Abstract",
            "Project Narrative",
            "Work Plan",
            "Evaluation Plan",
            "Organizational Capacity",
            "Budget Narrative",
        ],
        "Department of Education": [
            "Project Abstract",
            "Project Narrative",
            "Management Plan",
            "Evaluation Plan",
            "Budget Narrative",
            "References and Attachments",
        ],
        "USDA NIFA": [
            "Project Summary",
            "Project Narrative",
            "Management Plan",
            "Evaluation Plan",
            "Data Management Plan",
            "Budget Justification",
        ],
        "Department of Justice / National Institute of Justice": [
            "Proposal Abstract",
            "Program Narrative",
            "Goals Objectives and Deliverables",
            "Capabilities and Competencies",
            "Plan for Collecting Data",
            "Budget Narrative",
        ],
        "Department of State": [
            "Proposal Summary",
            "Statement of Need",
            "Project Activities",
            "Monitoring and Evaluation Plan",
            "Sustainability Plan",
            "Budget Narrative",
        ],
    }
    return plans.get(
        funder,
        [
            "Project Abstract",
            "Statement of Need",
            "Project Design and Work Plan",
            "Evaluation Plan",
            "Organizational Capacity",
            "Budget Narrative",
        ],
    )


def render_draft_section(
    section_name: str,
    profile: dict[str, Any],
    requirements: dict[str, Any],
    opportunity: Opportunity,
    readiness_item: dict[str, Any] | None,
    mode: str,
    use_llm: bool,
    llm_model: str,
) -> str:
    opportunity_number = profile.get("opportunity_number", opportunity.opportunity_folder)
    likely_applicant = profile.get("likely_applicant", opportunity.applicant_folder)
    title = profile.get("opportunity_title", "[CONFIRM]")
    readiness_status = readiness_item.get("status") if readiness_item else "[CONFIRM]"
    blocker = readiness_item.get("blocker_reason") if readiness_item else None
    next_step = readiness_item.get("recommended_next_step") if readiness_item else "[TODO] Determine next step."
    requirement_names = [
        item.get("name", "")
        for item in requirements.get("required_documents", [])
        if isinstance(item, dict)
    ]
    requirement_preview = ", ".join(requirement_names[:6]) if requirement_names else "[TODO]"
    source_ref = infer_requirement_source(requirements)
    narrative = select_narrative(mode, section_name, likely_applicant, opportunity_number, blocker, next_step)

    llm_text = generate_section_with_openai(
        use_llm=use_llm,
        model=llm_model,
        prompt=build_llm_prompt(
            section_name=section_name,
            profile=profile,
            mode=mode,
            source_ref=source_ref,
            blocker=blocker,
            next_step=next_step,
        ),
    )
    if llm_text:
        narrative = llm_text

    return f"""# {section_name}

Opportunity Number: `{opportunity_number}`
Opportunity Title: `{title}`
Applicant: `{likely_applicant}`
Draft mode: `{mode}`
Readiness status: `{readiness_status}`
Blocking issue: `{blocker or 'None'}`

## Draft Narrative

{narrative}

## Required Data for Finalization

- [CONFIRM] Exact section guidance and page limit from official NOFO/solicitation.
- [CONFIRM] Opportunity-specific priorities and scoring criteria language.
- [CONFIRM] Named project personnel, partner organizations, and authorized official details.
- [CONFIRM] Final budget values, fringe assumptions, indirect cost treatment, and match rules.
- [CONFIRM] Readiness next step: {next_step}

## Source Alignment Notes

- This section aligns to required-component signals including: `{requirement_preview}`.
- Primary source reference for this draft: `{source_ref}`.
- Replace placeholders after validating official source requirements in `Sources/source_index.md`.
- Do not submit until all items in `Analysis/human_review_todo.md` are resolved.
"""


def opening_paragraph(section_name: str, likely_applicant: str, opportunity_number: str) -> str:
    return (
        f"{likely_applicant} proposes this {section_name.lower()} for opportunity {opportunity_number} "
        "to deliver a measurable and sustainable program response aligned with funder priorities. "
        "The proposed work plan is designed to produce documented outcomes, transparent governance, "
        "and compliant grant administration from award start through closeout."
    )


def middle_paragraph(section_name: str, likely_applicant: str) -> str:
    if "budget" in section_name.lower():
        return (
            f"{likely_applicant} will maintain a cost framework that ties personnel, contracts, travel, "
            "technology, and indirect costs to specific project tasks and deliverables. The budget narrative "
            "will identify assumptions, document allowability, and separate confirmed values from items that "
            "remain under confirmation."
        )
    if "evaluation" in section_name.lower():
        return (
            "Evaluation activities will include baseline measurement, milestone tracking, quality assurance, "
            "and outcome reporting with clear indicators and data governance controls. The evaluation timeline "
            "will align with annual reporting obligations and include corrective-action triggers where needed."
        )
    return (
        "Implementation will follow a phased approach that includes startup, delivery, monitoring, and "
        "sustainability actions. Each phase will define accountable roles, expected outputs, and compliance "
        "checkpoints to support strong program performance and complete submission documentation."
    )


def closing_paragraph(section_name: str) -> str:
    return (
        f"This draft {section_name.lower()} is intended for grant-writer refinement and final compliance review. "
        "All factual fields, regulatory references, and submission-specific requirements should be verified "
        "against the official funding notice and policy guidance before final submission."
    )


def select_narrative(
    mode: str,
    section_name: str,
    likely_applicant: str,
    opportunity_number: str,
    blocker: str | None,
    next_step: str,
) -> str:
    if mode == "blocked_on_admin_data":
        return (
            f"{likely_applicant} cannot finalize this {section_name.lower()} for {opportunity_number} using currently "
            "available public and local-source information. This section requires organization-administered "
            "or person-specific data that is not yet present in the workspace.\n\n"
            f"Blocking condition: {blocker or '[CONFIRM] Missing administrative source details.'}\n\n"
            f"Interim action: {next_step}\n\n"
            "Preparation notes: maintain section heading structure, collect required data from grant administrator "
            "or authorized personnel, and regenerate this section after confirmations are complete."
        )
    if mode == "blocked_on_official_source":
        return (
            f"{likely_applicant} can only provide a structured outline for this {section_name.lower()} until the "
            "official funder NOFO/solicitation and policy guidance are verified.\n\n"
            "Interim outline:\n"
            "1. Required heading structure aligned to funder instructions.\n"
            "2. Core applicant response points and deliverable commitments.\n"
            "3. Compliance elements (page limits, forms, review criteria) pending source confirmation.\n\n"
            f"Next step: {next_step}"
        )
    base = "\n\n".join(
        [
            opening_paragraph(section_name, likely_applicant, opportunity_number),
            middle_paragraph(section_name, likely_applicant),
            closing_paragraph(section_name),
        ]
    )
    if mode == "partial_admin_pending":
        return (
            base
            + "\n\n"
            + "This section is partially complete but requires additional administrator-confirmed data "
            "before final submission packaging."
        )
    return base


def resolve_readiness_for_section(section_name: str, readiness: dict[str, Any]) -> dict[str, Any] | None:
    items = readiness.get("documents", [])
    if not isinstance(items, list):
        return None
    target = normalize_name(section_name)
    for item in items:
        if not isinstance(item, dict):
            continue
        name = normalize_name(str(item.get("name", "")))
        if target == name:
            return item
    for item in items:
        if not isinstance(item, dict):
            continue
        name = normalize_name(str(item.get("name", "")))
        if target in name or name in target:
            return item
    return None


def drafting_mode_from_readiness(readiness_item: dict[str, Any] | None) -> str:
    if not readiness_item:
        return "standard_realistic_draft"
    status = str(readiness_item.get("status", ""))
    if status == "not_started_blocked_on_admin_data":
        return "blocked_on_admin_data"
    if status == "not_started_blocked_on_official_source":
        return "blocked_on_official_source"
    if status == "drafted_but_blocked_on_admin_data":
        return "partial_admin_pending"
    return "standard_realistic_draft"


def infer_requirement_source(requirements: dict[str, Any]) -> str:
    required = requirements.get("required_documents", [])
    for item in required:
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        if isinstance(source, str) and source.strip():
            return source
    return "[CONFIRM] Official source URL required"


def build_llm_prompt(
    *,
    section_name: str,
    profile: dict[str, Any],
    mode: str,
    source_ref: str,
    blocker: str | None,
    next_step: str,
) -> str:
    return f"""
You are assisting with grant drafting.

Generate a professional grant document section in markdown.
Section: {section_name}
Funder: {profile.get("funder", "[CONFIRM]")}
Opportunity Number: {profile.get("opportunity_number", "[CONFIRM]")}
Applicant: {profile.get("likely_applicant", "[CONFIRM]")}
Mode: {mode}
Source reference: {source_ref}
Blocking condition: {blocker or "None"}
Next step: {next_step}

Rules:
- Do not fabricate factual details.
- Use [CONFIRM] placeholders for unknown specifics.
- Keep a funder-facing, submission-style tone.
- If blocked, produce a realistic interim draft/outline that explicitly identifies missing inputs.
"""


def normalize_name(value: str) -> str:
    cleaned = (
        value.lower()
        .replace("&", "and")
        .replace("/", " ")
        .replace("-", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(",", " ")
        .strip()
    )
    return re.sub(r"\s+", " ", cleaned)


def slugify(value: str) -> str:
    return (
        value.lower()
        .replace("&", "and")
        .replace("/", " ")
        .replace("-", " ")
        .strip()
        .replace("  ", " ")
        .replace(" ", "_")
    )
