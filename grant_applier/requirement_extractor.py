"""Requirement extraction from discovered sources and local files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .analyzer import render_yaml
from .discovery import Opportunity, list_local_source_files
from .document_parser import read_text_from_file
from .profiles import ensure_profile


FUNDING_DOCS_BY_FUNDER: dict[str, list[str]] = {
    "National Science Foundation": [
        "Project Summary",
        "Project Description",
        "References Cited",
        "Data Management and Sharing Plan",
        "Facilities, Equipment, and Other Resources",
        "Budget Justification",
        "Biographical Sketches",
        "Current and Pending (Other) Support",
        "Project Personnel and Partner Organizations",
        "Letters of Collaboration",
    ],
    "HHS / ACL / NIDILRR": [
        "Project Abstract",
        "Project Narrative",
        "Work Plan",
        "Evaluation Plan",
        "Organizational Capacity",
        "Budget Narrative",
        "Required federal forms and assurances",
    ],
    "Department of Education": [
        "Project Abstract",
        "Project Narrative aligned to selection criteria",
        "Management Plan",
        "Evaluation Plan",
        "Budget Narrative",
        "GEPA statement and assurances",
    ],
    "USDA NIFA": [
        "Project Summary",
        "Project Narrative",
        "Management Plan",
        "Evaluation Plan",
        "Budget Justification",
        "Data Management Plan (if required)",
    ],
    "Department of Justice / National Institute of Justice": [
        "Proposal Abstract",
        "Program Narrative",
        "Goals, Objectives, and Deliverables",
        "Capabilities and Competencies",
        "Plan for Collecting Data",
        "Budget Detail Worksheet and Narrative",
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


def extract_requirements(
    opportunity: Opportunity,
    overwrite: bool = False,
) -> dict[str, Any]:
    profile = ensure_profile(opportunity, overwrite=False)
    sources = load_sources(opportunity)
    local_files = list_local_source_files(opportunity.path)

    extracted_signals = extract_local_signals(local_files)
    inferred_documents = FUNDING_DOCS_BY_FUNDER.get(
        str(profile.get("funder", "[CONFIRM]")),
        [
            "Project Abstract",
            "Project Narrative",
            "Budget Narrative",
            "Required forms and attachments",
        ],
    )

    requirements = {
        "source_confidence": {
            "official_source_verified": any(
                source.get("source_type") == "official_funder_page" and source.get("verified")
                for source in sources
            ),
            "local_requirement_doc_found": extracted_signals["local_requirement_doc_found"],
        },
        "required_documents": [
            {
                "name": doc_name,
                "required": True,
                "status": "inferred_template_until_officially_confirmed",
                "source": infer_document_source(sources),
            }
            for doc_name in inferred_documents
        ],
        "page_limit_signals": extracted_signals["page_limits"],
        "deadline_signals": extracted_signals["deadlines"],
        "budget_rules": [
            {
                "rule": "[CONFIRM] Verify allowable costs, indirect cost treatment, and match/cost share.",
                "source": infer_document_source(sources),
            }
        ],
        "eligibility_rules": [
            {
                "rule": "[CONFIRM] Verify applicant eligibility from official NOFO and policy guide.",
                "source": infer_document_source(sources),
            }
        ],
        "review_criteria": [
            {
                "criterion": "[TODO] Extract official review criteria text and scoring structure.",
                "source": infer_document_source(sources),
            }
        ],
        "formatting_rules": [
            {
                "rule": signal,
                "source": "local_source_text",
            }
            for signal in extracted_signals["formatting"]
        ],
    }

    write_requirement_outputs(opportunity, requirements, overwrite=overwrite)
    update_analysis_markdown(opportunity, requirements)
    update_profile_from_requirements(opportunity, profile, requirements)
    return requirements


def load_sources(opportunity: Opportunity) -> list[dict[str, Any]]:
    path = opportunity.path / "Sources" / "sources.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
    except json.JSONDecodeError:
        return []
    return []


def extract_local_signals(local_files: list[Path]) -> dict[str, Any]:
    page_limit_pattern = re.compile(r"\b(\d{1,3})\s*page(s)?\b", re.IGNORECASE)
    due_pattern = re.compile(
        r"\b(due|deadline|application due)\b.{0,40}\b("
        r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
        r")[a-z]*\s+\d{1,2},?\s+\d{4}",
        re.IGNORECASE,
    )
    formatting_pattern = re.compile(
        r"\b(12-point|11-point|font|margins?|single-spaced|double-spaced)\b", re.IGNORECASE
    )

    page_limits: list[str] = []
    deadlines: list[str] = []
    formatting: list[str] = []
    local_requirement_doc_found = False

    for file_path in local_files:
        lower_name = file_path.name.lower()
        if any(token in lower_name for token in ("requirement", "instruction", "guideline", "solicitation")):
            local_requirement_doc_found = True
        text = read_text_from_file(file_path)
        if not text:
            continue
        for match in page_limit_pattern.finditer(text):
            snippet = compact_snippet(text, match.start(), match.end())
            if snippet not in page_limits:
                page_limits.append(snippet)
        for match in due_pattern.finditer(text):
            snippet = compact_snippet(text, match.start(), match.end())
            if snippet not in deadlines:
                deadlines.append(snippet)
        for match in formatting_pattern.finditer(text):
            snippet = compact_snippet(text, match.start(), match.end())
            if snippet not in formatting:
                formatting.append(snippet)

    if not page_limits:
        page_limits.append("[CONFIRM] Page limits not yet extracted from authoritative source.")
    if not deadlines:
        deadlines.append("[CONFIRM] Deadline not yet extracted from authoritative source.")
    if not formatting:
        formatting.append("[CONFIRM] Formatting requirements not yet extracted from authoritative source.")

    return {
        "page_limits": page_limits[:20],
        "deadlines": deadlines[:20],
        "formatting": formatting[:20],
        "local_requirement_doc_found": local_requirement_doc_found,
    }


def compact_snippet(text: str, start: int, end: int) -> str:
    left = max(0, start - 60)
    right = min(len(text), end + 60)
    snippet = text[left:right].replace("\n", " ").replace("\t", " ")
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet


def infer_document_source(sources: list[dict[str, Any]]) -> str:
    for source in sources:
        if source.get("source_type") == "official_funder_page" and source.get("verified"):
            return str(source.get("url"))
    for source in sources:
        if source.get("url"):
            return str(source.get("url"))
    return "[CONFIRM] Official source URL required"


def write_requirement_outputs(
    opportunity: Opportunity,
    requirements: dict[str, Any],
    overwrite: bool,
) -> None:
    analysis_dir = opportunity.path / "Analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    json_path = analysis_dir / "requirements.json"
    if overwrite or not json_path.exists():
        json_path.write_text(json.dumps(requirements, indent=2), encoding="utf-8")

    yaml_path = analysis_dir / "requirements.yaml"
    if overwrite or not yaml_path.exists():
        yaml_path.write_text(render_yaml(requirements).rstrip() + "\n", encoding="utf-8")


def update_analysis_markdown(opportunity: Opportunity, requirements: dict[str, Any]) -> None:
    analysis_dir = opportunity.path / "Analysis"
    required_documents_path = analysis_dir / "required_documents.md"
    review_criteria_path = analysis_dir / "review_criteria.md"
    compliance_path = analysis_dir / "compliance_checklist.md"
    human_todo_path = analysis_dir / "human_review_todo.md"

    required_lines = [
        "# Required Documents",
        "",
        "Status: `draft_not_submission_ready`",
        "",
        "## Required Components",
        "",
    ]
    for item in requirements["required_documents"]:
        required_lines.append(
            f"- `{item['name']}` | status: `{item['status']}` | source: {item['source']}"
        )
    required_lines.extend(
        [
            "",
            "## Signals From Local Sources",
            "",
            "### Page Limits",
            "",
        ]
    )
    for signal in requirements["page_limit_signals"]:
        required_lines.append(f"- {signal}")
    required_lines.extend(["", "### Formatting Signals", ""])
    for signal in requirements["formatting_rules"]:
        required_lines.append(f"- {signal['rule']}")
    required_documents_path.write_text("\n".join(required_lines).rstrip() + "\n", encoding="utf-8")

    review_lines = ["# Review Criteria", ""]
    for item in requirements["review_criteria"]:
        review_lines.append(f"- {item['criterion']} (source: {item['source']})")
    review_criteria_path.write_text("\n".join(review_lines).rstrip() + "\n", encoding="utf-8")

    compliance_lines = [
        "# Compliance Checklist",
        "",
        "- [ ] Confirm every required document has final content and source citation.",
        "- [ ] Confirm page limits and formatting requirements from official guidance.",
        "- [ ] Confirm budget and indirect cost rules from official guidance.",
        "- [ ] Confirm eligibility and submission mechanism.",
        "- [ ] Confirm all required federal forms and certifications.",
    ]
    compliance_path.write_text("\n".join(compliance_lines).rstrip() + "\n", encoding="utf-8")

    todo_lines = [
        "# Human Review TODO",
        "",
        "- [ ] Confirm authoritative NOFO and policy URLs.",
        "- [ ] Confirm exact due date and submission time zone.",
        "- [ ] Confirm applicant eligibility and partnering structure.",
        "- [ ] Confirm indirect cost rate and budget rules.",
        "- [ ] Confirm all required forms and attachments are complete.",
        "",
        "## Deadline Signals",
        "",
    ]
    for signal in requirements["deadline_signals"]:
        todo_lines.append(f"- {signal}")
    human_todo_path.write_text("\n".join(todo_lines).rstrip() + "\n", encoding="utf-8")


def update_profile_from_requirements(
    opportunity: Opportunity,
    profile: dict[str, Any],
    requirements: dict[str, Any],
) -> None:
    profile.setdefault("source_status", {})
    profile["source_status"]["full_nofo_found"] = bool(
        profile["source_status"].get("full_nofo_found", False)
        or requirements["source_confidence"]["official_source_verified"]
    )
    profile["human_review_required"] = True

    analysis_dir = opportunity.path / "Analysis"
    (analysis_dir / "opportunity_profile.json").write_text(
        json.dumps(profile, indent=2), encoding="utf-8"
    )
    (analysis_dir / "opportunity_profile.yaml").write_text(
        render_yaml(profile).rstrip() + "\n", encoding="utf-8"
    )
