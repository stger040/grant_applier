"""Draft generation for opportunity narrative packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .discovery import Opportunity
from .profiles import ensure_profile


def generate_drafts(opportunity: Opportunity, overwrite: bool = False) -> list[Path]:
    profile = ensure_profile(opportunity, overwrite=False)
    requirements = load_requirements(opportunity)
    drafts_dir = opportunity.path / "Drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    sections = section_plan_for_funder(str(profile.get("funder", "[CONFIRM]")))
    created: list[Path] = []
    for index, section in enumerate(sections, start=1):
        filename = f"{index:02d}_{slugify(section)}.md"
        path = drafts_dir / filename
        if path.exists() and not overwrite:
            continue
        path.write_text(
            render_draft_section(
                section_name=section,
                profile=profile,
                requirements=requirements,
                opportunity=opportunity,
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


def section_plan_for_funder(funder: str) -> list[str]:
    plans = {
        "National Science Foundation": [
            "Project Summary",
            "Project Description",
            "Budget Justification",
            "Data Management and Sharing Plan",
            "Facilities Equipment and Other Resources",
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
) -> str:
    opportunity_number = profile.get("opportunity_number", opportunity.opportunity_folder)
    likely_applicant = profile.get("likely_applicant", opportunity.applicant_folder)
    title = profile.get("opportunity_title", "[CONFIRM]")
    requirement_names = [
        item.get("name", "")
        for item in requirements.get("required_documents", [])
        if isinstance(item, dict)
    ]
    requirement_preview = ", ".join(requirement_names[:6]) if requirement_names else "[TODO]"

    return f"""# {section_name}

Opportunity Number: `{opportunity_number}`
Opportunity Title: `{title}`
Applicant: `{likely_applicant}`

## Draft Narrative

{opening_paragraph(section_name, likely_applicant, opportunity_number)}

{middle_paragraph(section_name, likely_applicant)}

{closing_paragraph(section_name)}

## Required Data for Finalization

- [CONFIRM] Exact section guidance and page limit from official NOFO/solicitation.
- [CONFIRM] Opportunity-specific priorities and scoring criteria language.
- [CONFIRM] Named project personnel, partner organizations, and authorized official details.
- [CONFIRM] Final budget values, fringe assumptions, indirect cost treatment, and match rules.

## Source Alignment Notes

- This section aligns to required-component signals including: `{requirement_preview}`.
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
