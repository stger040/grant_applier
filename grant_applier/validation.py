"""Compliance validation for generated opportunity workspaces."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .discovery import Opportunity
from .profiles import ensure_profile


CORE_REQUIRED_FILES = [
    "Sources/source_index.md",
    "Sources/sources.json",
    "Analysis/opportunity_profile.yaml",
    "Analysis/opportunity_profile.json",
    "Analysis/required_documents.md",
    "Analysis/requirements.json",
    "Analysis/document_readiness.json",
    "Analysis/document_readiness.md",
    "Analysis/eligibility_assessment.md",
    "Analysis/compliance_checklist.md",
    "Analysis/human_review_todo.md",
    "Compliance/final_submission_checklist.md",
]


def validate_opportunity(opportunity: Opportunity, overwrite: bool = True) -> dict[str, Any]:
    profile = ensure_profile(opportunity, overwrite=False)
    missing_files = [
        path for path in CORE_REQUIRED_FILES if not (opportunity.path / path).exists()
    ]

    draft_files = sorted((opportunity.path / "Drafts").glob("*.md"))
    if not draft_files:
        missing_files.append("Drafts/*.md")

    budget_files = sorted((opportunity.path / "Budgets").glob("*.xlsx"))
    if not budget_files:
        missing_files.append("Budgets/*.xlsx")

    placeholders = collect_placeholders(opportunity.path)
    source_warnings = source_citation_warnings(opportunity.path)
    readiness = load_readiness(opportunity.path)
    readiness_warnings = readiness_blocker_warnings(readiness)
    completion_score = compute_completion_score(
        missing_count=len(missing_files),
        placeholder_count=len(placeholders),
        source_warning_count=len(source_warnings),
        readiness=readiness,
    )

    report = {
        "status": "draft_not_submission_ready",
        "opportunity": opportunity.relative_id,
        "funder": profile.get("funder", "[CONFIRM]"),
        "completion_score": completion_score,
        "missing_items": missing_files,
        "placeholders_remaining": placeholders,
        "page_limit_warnings": ["[CONFIRM] Page limit validation requires official source extraction."],
        "source_citation_warnings": source_warnings,
        "readiness_warnings": readiness_warnings,
        "eligibility_warnings": [
            "[CONFIRM] Eligibility must be confirmed from official NOFO and policy guidance."
        ],
    }

    write_validation_outputs(opportunity, report, overwrite=overwrite)
    return report


def collect_placeholders(opportunity_path: Path) -> list[str]:
    pattern = re.compile(r"\[(?:CONFIRM|TODO|INSERT)[^\]]*\]")
    findings: list[str] = []
    for rel_path in [
        Path("Analysis/required_documents.md"),
        Path("Analysis/human_review_todo.md"),
        Path("Analysis/opportunity_profile.yaml"),
    ]:
        file_path = opportunity_path / rel_path
        if not file_path.exists():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for match in pattern.finditer(text):
            findings.append(f"{rel_path}: {match.group(0)}")
    return findings[:200]


def source_citation_warnings(opportunity_path: Path) -> list[str]:
    sources_path = opportunity_path / "Sources" / "sources.json"
    if not sources_path.exists():
        return ["Missing Sources/sources.json"]
    try:
        payload = json.loads(sources_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["Sources/sources.json is invalid JSON"]
    if not isinstance(payload, list):
        return ["Sources/sources.json must be a list of source records"]
    if not any(record.get("source_type") == "official_funder_page" for record in payload if isinstance(record, dict)):
        return ["No verified official funder page in Sources/sources.json"]
    return []


def load_readiness(opportunity_path: Path) -> dict[str, Any]:
    path = opportunity_path / "Analysis" / "document_readiness.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        return {}
    return {}


def readiness_blocker_warnings(readiness: dict[str, Any]) -> list[str]:
    if not readiness:
        return ["Document readiness matrix missing or unreadable."]
    warnings: list[str] = []
    documents = readiness.get("documents", [])
    if not isinstance(documents, list):
        return ["Document readiness matrix invalid format."]
    blocking_statuses = {
        "drafted_but_blocked_on_admin_data",
        "not_started_blocked_on_admin_data",
        "not_started_blocked_on_official_source",
    }
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        status = str(doc.get("status", ""))
        if status in blocking_statuses:
            warnings.append(f"{doc.get('name', '[CONFIRM]')}: {status}")
    return warnings


def compute_completion_score(
    *,
    missing_count: int,
    placeholder_count: int,
    source_warning_count: int,
    readiness: dict[str, Any],
) -> float:
    score = 100.0
    score -= missing_count * 7.5
    score -= min(placeholder_count, 40) * 0.8
    score -= source_warning_count * 8.0

    summary = readiness.get("summary", {}) if isinstance(readiness, dict) else {}
    blocked_docs = int(summary.get("blocked_document_count", 0) or 0)
    score -= blocked_docs * 3.0
    return round(max(0.0, min(100.0, score)), 2)


def write_validation_outputs(opportunity: Opportunity, report: dict[str, Any], overwrite: bool) -> None:
    compliance_dir = opportunity.path / "Compliance"
    compliance_dir.mkdir(parents=True, exist_ok=True)

    report_path = compliance_dir / "validation_report.json"
    if overwrite or not report_path.exists():
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    checklist_path = compliance_dir / "final_submission_checklist.md"
    checklist = render_final_submission_checklist(report)
    if overwrite or not checklist_path.exists():
        checklist_path.write_text(checklist.rstrip() + "\n", encoding="utf-8")
    else:
        checklist_path.write_text(checklist.rstrip() + "\n", encoding="utf-8")


def render_final_submission_checklist(report: dict[str, Any]) -> str:
    missing = report.get("missing_items", [])
    placeholders = report.get("placeholders_remaining", [])
    source_warnings = report.get("source_citation_warnings", [])
    readiness_warnings = report.get("readiness_warnings", [])

    lines = [
        "# Final Submission Checklist",
        "",
        f"Status: `{report.get('status', 'draft_not_submission_ready')}`",
        f"Estimated completion score: `{report.get('completion_score', '[CONFIRM]')}`",
        "",
        "## Blocking Items",
        "",
    ]
    if missing:
        for item in missing:
            lines.append(f"- [ ] Missing required artifact: `{item}`")
    else:
        lines.append("- [ ] [CONFIRM] No missing required artifacts detected.")

    lines.extend(["", "## Placeholder Review", ""])
    if placeholders:
        for item in placeholders[:30]:
            lines.append(f"- [ ] Resolve placeholder: {item}")
    else:
        lines.append("- [ ] [CONFIRM] Placeholder scan returned no unresolved markers.")

    lines.extend(["", "## Source Validation", ""])
    if source_warnings:
        for warning in source_warnings:
            lines.append(f"- [ ] Resolve source warning: {warning}")
    else:
        lines.append("- [ ] Confirm all requirements have official source citations.")

    lines.extend(["", "## Document Readiness Blockers", ""])
    if readiness_warnings:
        for warning in readiness_warnings:
            lines.append(f"- [ ] Resolve readiness blocker: {warning}")
    else:
        lines.append("- [ ] [CONFIRM] No document-level blockers found in readiness matrix.")

    lines.extend(
        [
            "",
            "## Final Human Confirmations",
            "",
            "- [ ] Authorized representative and submission credentials confirmed.",
            "- [ ] Deadline/time zone confirmed.",
            "- [ ] Eligibility confirmed.",
            "- [ ] Budget and indirect cost treatment confirmed.",
            "- [ ] Required forms and attachments completed.",
        ]
    )
    return "\n".join(lines)
