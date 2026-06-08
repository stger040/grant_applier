"""Document-level readiness and rigor scoring utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .discovery import Opportunity


NSF_26_509_RIGOR_BENCHMARK: list[dict[str, Any]] = [
    {
        "name": "Project Summary",
        "status_example": "Drafted",
        "notes": "1 page",
    },
    {
        "name": "Project Description",
        "status_example": "Drafted",
        "notes": "20 pages max for Category II",
    },
    {
        "name": "References Cited",
        "status_example": "Drafted",
        "notes": "No page limit",
    },
    {
        "name": "Budget Forms",
        "status_example": "Draft spreadsheets created; final numbers need confirmation",
        "notes": "AAIP lead + SGDI subaward",
    },
    {
        "name": "Budget Justification",
        "status_example": "AAIP drafted; SGDI subaward justification still needed",
        "notes": "Narrative justification",
    },
    {
        "name": "Biographical Sketches",
        "status_example": "Still needed",
        "notes": "Likely generated via SciENcv",
    },
    {
        "name": "Current and Pending (Other) Support",
        "status_example": "Still needed",
        "notes": "Person-specific",
    },
    {
        "name": "Facilities, Equipment, and Other Resources",
        "status_example": "Drafted",
        "notes": "",
    },
    {
        "name": "Data Management and Sharing Plan",
        "status_example": "Drafted",
        "notes": "2 pages max",
    },
    {
        "name": "Collaborators and Other Affiliations",
        "status_example": "Still needed",
        "notes": "NSF single-copy form; person-specific",
    },
    {
        "name": "Detailed Cost Estimate Supplement",
        "status_example": "Drafted",
        "notes": "Required for Category II",
    },
    {
        "name": "Project Personnel and Partner Organizations",
        "status_example": "Still needed",
        "notes": "Required by NSF 26-509",
    },
]


READINESS_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "National Science Foundation": [
        {
            "name": "Project Summary",
            "page_limit": "1 page",
            "artifact_keywords": ["project summary"],
            "admin_blockers": [],
            "requires_official_source": True,
        },
        {
            "name": "Project Description",
            "page_limit": "[CONFIRM]",
            "artifact_keywords": ["project description", "project narrative"],
            "admin_blockers": [],
            "requires_official_source": True,
        },
        {
            "name": "References Cited",
            "page_limit": "No page limit",
            "artifact_keywords": ["references cited", "references"],
            "admin_blockers": [],
            "requires_official_source": False,
        },
        {
            "name": "Budget Forms",
            "page_limit": "N/A",
            "artifact_keywords": ["budget", "sf-424"],
            "admin_blockers": ["final salary rates", "fringe rates", "indirect cost agreement"],
            "requires_official_source": True,
        },
        {
            "name": "Budget Justification",
            "page_limit": "[CONFIRM]",
            "artifact_keywords": ["budget justification"],
            "admin_blockers": ["final salary/fringe/indirect values", "subaward detail finalization"],
            "requires_official_source": True,
        },
        {
            "name": "Biographical Sketches",
            "page_limit": "[CONFIRM]",
            "artifact_keywords": ["biosketch", "biographical sketch"],
            "admin_blockers": ["individual PI/co-PI/senior personnel data", "SciENcv export"],
            "requires_official_source": False,
            "minimum_artifact_count": 2,
        },
        {
            "name": "Current and Pending (Other) Support",
            "page_limit": "[CONFIRM]",
            "artifact_keywords": ["current and pending", "other support"],
            "admin_blockers": ["person-specific support records for each senior person"],
            "requires_official_source": False,
            "minimum_artifact_count": 2,
        },
        {
            "name": "Facilities, Equipment, and Other Resources",
            "page_limit": "[CONFIRM]",
            "artifact_keywords": ["facilities", "equipment", "other resources"],
            "admin_blockers": [],
            "requires_official_source": False,
        },
        {
            "name": "Data Management and Sharing Plan",
            "page_limit": "2 pages (NSF typical; [CONFIRM])",
            "artifact_keywords": ["data management", "sharing plan"],
            "admin_blockers": [],
            "requires_official_source": True,
        },
        {
            "name": "Collaborators and Other Affiliations",
            "page_limit": "[CONFIRM]",
            "artifact_keywords": ["collaborators", "affiliations", "coa"],
            "admin_blockers": ["COA details for each senior person"],
            "requires_official_source": False,
            "minimum_artifact_count": 2,
        },
        {
            "name": "Detailed Cost Estimate Supplement",
            "page_limit": "[CONFIRM]",
            "artifact_keywords": ["detailed cost estimate"],
            "admin_blockers": ["category-level cost basis finalization"],
            "requires_official_source": True,
        },
        {
            "name": "Project Personnel and Partner Organizations",
            "page_limit": "[CONFIRM]",
            "artifact_keywords": ["project personnel", "partner organizations"],
            "admin_blockers": ["final named personnel and partner roster"],
            "requires_official_source": True,
        },
    ]
}


GENERIC_READINESS_TEMPLATE: list[dict[str, Any]] = [
    {
        "name": "Project Abstract",
        "page_limit": "[CONFIRM]",
        "artifact_keywords": ["abstract"],
        "admin_blockers": [],
        "requires_official_source": True,
    },
    {
        "name": "Project Narrative",
        "page_limit": "[CONFIRM]",
        "artifact_keywords": ["narrative", "description"],
        "admin_blockers": [],
        "requires_official_source": True,
    },
    {
        "name": "Budget Narrative",
        "page_limit": "[CONFIRM]",
        "artifact_keywords": ["budget narrative", "budget justification"],
        "admin_blockers": ["final budget values", "indirect cost confirmation"],
        "requires_official_source": True,
    },
    {
        "name": "Required Federal Forms and Attachments",
        "page_limit": "[CONFIRM]",
        "artifact_keywords": ["forms", "attachments", "assurances"],
        "admin_blockers": ["authorized representative data", "registration details"],
        "requires_official_source": True,
    },
]


ADMIN_SIGNAL_KEYWORDS = {
    "pi/co-pi/senior roster": ("pi", "co-pi", "senior personnel", "project personnel"),
    "biosketch data": ("biosketch", "sciencv"),
    "current/pending support records": ("current and pending", "other support"),
    "coa records": ("collaborators", "affiliations", "coa"),
    "final budget rates": ("fringe", "salary", "indirect", "rate agreement"),
}


def collect_artifact_paths(opportunity: Opportunity) -> list[str]:
    files: list[str] = []
    for path in opportunity.path.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(opportunity.path)
        if any(part in {"Analysis", "Sources", "Compliance"} for part in rel.parts):
            continue
        files.append(str(rel))
    return sorted(files, key=str.lower)


def build_document_readiness(
    opportunity: Opportunity,
    profile: dict[str, Any],
    requirements: dict[str, Any],
    local_file_paths: list[str],
) -> dict[str, Any]:
    funder = str(profile.get("funder", "[CONFIRM]"))
    template = READINESS_TEMPLATES.get(funder, GENERIC_READINESS_TEMPLATE)
    source_verified = bool(
        requirements.get("source_confidence", {}).get("official_source_verified", False)
    )
    lower_files = [path.lower() for path in local_file_paths]
    admin_signals = detect_admin_signals(lower_files)

    documents: list[dict[str, Any]] = []
    for spec in template:
        artifact_count = count_keywords(lower_files, spec["artifact_keywords"])
        artifact_found = artifact_count > 0
        admin_required = bool(spec["admin_blockers"])
        admin_signal_present = has_admin_signal_for_doc(spec["name"], admin_signals)
        expected_artifacts = int(spec.get("minimum_artifact_count", 1) or 1)
        if opportunity.applicant_folder == "AAIP" and spec["name"] in {"Budget Forms", "Budget Justification"}:
            expected_artifacts = max(expected_artifacts, 2)
        coverage_complete, coverage_note = assess_doc_coverage(
            doc_name=spec["name"],
            lower_files=lower_files,
            applicant_folder=opportunity.applicant_folder,
            artifact_count=artifact_count,
            expected_artifacts=expected_artifacts,
        )
        status, blocker_reason, recommended_next = determine_status(
            artifact_found=artifact_found,
            source_verified=source_verified,
            admin_required=admin_required,
            admin_signal_present=admin_signal_present,
            requires_official_source=bool(spec["requires_official_source"]),
            admin_blockers=spec["admin_blockers"],
            coverage_complete=coverage_complete,
            coverage_note=coverage_note,
        )
        documents.append(
            {
                "name": spec["name"],
                "page_limit": spec["page_limit"],
                "artifact_found": artifact_found,
                "artifact_count": artifact_count,
                "expected_artifacts": expected_artifacts,
                "coverage_complete": coverage_complete,
                "coverage_note": coverage_note,
                "status": status,
                "requires_admin_data": admin_required,
                "admin_data_signal_present": admin_signal_present,
                "blocker_reason": blocker_reason,
                "recommended_next_step": recommended_next,
            }
        )

    summary = summarize_document_status(documents)
    return {
        "opportunity": opportunity.relative_id,
        "funder": funder,
        "source_verified": source_verified,
        "admin_signal_inventory": admin_signals,
        "summary": summary,
        "documents": documents,
        "benchmark_reference": (
            NSF_26_509_RIGOR_BENCHMARK if funder == "National Science Foundation" else []
        ),
    }


def detect_admin_signals(lower_files: list[str]) -> dict[str, bool]:
    inventory: dict[str, bool] = {}
    for signal_name, keywords in ADMIN_SIGNAL_KEYWORDS.items():
        inventory[signal_name] = any(keyword in file_path for keyword in keywords for file_path in lower_files)
    return inventory


def has_admin_signal_for_doc(doc_name: str, admin_signals: dict[str, bool]) -> bool:
    key = doc_name.lower()
    if "biographical sketch" in key:
        return admin_signals.get("biosketch data", False)
    if "current and pending" in key or "other support" in key:
        return admin_signals.get("current/pending support records", False)
    if "affiliations" in key or "collaborators" in key:
        return admin_signals.get("coa records", False)
    if "project personnel" in key:
        return admin_signals.get("pi/co-pi/senior roster", False)
    if "budget" in key or "cost estimate" in key:
        return admin_signals.get("final budget rates", False)
    return True


def determine_status(
    artifact_found: bool,
    source_verified: bool,
    admin_required: bool,
    admin_signal_present: bool,
    requires_official_source: bool,
    admin_blockers: list[str],
    coverage_complete: bool,
    coverage_note: str | None,
) -> tuple[str, str | None, str]:
    if artifact_found and not coverage_complete:
        return (
            "drafted_but_blocked_on_admin_data",
            coverage_note or "Artifact set is incomplete for required coverage.",
            "Collect missing document coverage and regenerate this component.",
        )
    if artifact_found and (not admin_required or admin_signal_present):
        return (
            "drafted",
            None,
            "Perform final compliance review and page-limit check.",
        )
    if artifact_found and admin_required and not admin_signal_present:
        return (
            "drafted_but_blocked_on_admin_data",
            "Draft exists but person-specific/admin data is incomplete.",
            "Collect missing admin/personnel data before finalizing.",
        )
    if not artifact_found and admin_required and not admin_signal_present:
        blocker = "; ".join(admin_blockers) if admin_blockers else "Required admin data missing."
        return (
            "not_started_blocked_on_admin_data",
            blocker,
            "Collect admin/personnel source data, then regenerate document.",
        )
    if not artifact_found and requires_official_source and not source_verified:
        return (
            "not_started_blocked_on_official_source",
            "Official funder source not yet verified.",
            "Verify official NOFO/policy source before generating final draft content.",
        )
    return (
        "ready_for_realistic_draft_generation",
        None,
        "Generate narrative draft using known facts and explicit placeholders.",
    )


def summarize_document_status(documents: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    for doc in documents:
        status = str(doc["status"])
        by_status[status] = by_status.get(status, 0) + 1
    ready_count = by_status.get("drafted", 0)
    blocked_count = (
        by_status.get("drafted_but_blocked_on_admin_data", 0)
        + by_status.get("not_started_blocked_on_admin_data", 0)
        + by_status.get("not_started_blocked_on_official_source", 0)
    )
    total = len(documents)
    readiness_ratio = (ready_count / total) if total else 0.0
    return {
        "total_required_documents": total,
        "by_status": by_status,
        "drafted_or_ready_ratio": round(readiness_ratio, 3),
        "blocked_document_count": blocked_count,
    }


def has_keywords(lower_files: list[str], keywords: list[str]) -> bool:
    return any(keyword in path for keyword in keywords for path in lower_files)


def count_keywords(lower_files: list[str], keywords: list[str]) -> int:
    matched = [
        path
        for path in lower_files
        if any(keyword in path for keyword in keywords)
    ]
    return len(set(matched))


def assess_doc_coverage(
    *,
    doc_name: str,
    lower_files: list[str],
    applicant_folder: str,
    artifact_count: int,
    expected_artifacts: int,
) -> tuple[bool, str | None]:
    if doc_name == "Budget Forms" and applicant_folder == "AAIP":
        aaip = any("aaip" in path and "budget" in path for path in lower_files)
        sgdi = any("sgdi" in path and "budget" in path for path in lower_files)
        if aaip and sgdi:
            return True, None
        return False, "AAIP and SGDI budget coverage is incomplete."

    if doc_name == "Budget Justification" and applicant_folder == "AAIP":
        aaip = any("aaip" in path and "budget justification" in path for path in lower_files)
        sgdi = any("sgdi" in path and "budget justification" in path for path in lower_files)
        if aaip and sgdi:
            return True, None
        return False, "AAIP and SGDI budget justification coverage is incomplete."

    if artifact_count >= expected_artifacts:
        return True, None
    return (
        False,
        f"Only {artifact_count} artifact(s) found; expected at least {expected_artifacts} for this component.",
    )


def write_document_readiness(opportunity: Opportunity, readiness: dict[str, Any]) -> None:
    analysis_dir = opportunity.path / "Analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    json_path = analysis_dir / "document_readiness.json"
    json_path.write_text(json.dumps(readiness, indent=2), encoding="utf-8")

    md_path = analysis_dir / "document_readiness.md"
    md_path.write_text(render_document_readiness_markdown(readiness).rstrip() + "\n", encoding="utf-8")


def render_document_readiness_markdown(readiness: dict[str, Any]) -> str:
    summary = readiness["summary"]
    lines = [
        "# Document Readiness Matrix",
        "",
        f"Opportunity: `{readiness['opportunity']}`",
        f"Funder: `{readiness['funder']}`",
        f"Official source verified: `{readiness['source_verified']}`",
        "",
        "## Summary",
        "",
        f"- Total required documents modeled: `{summary['total_required_documents']}`",
        f"- Blocked documents: `{summary['blocked_document_count']}`",
        f"- Drafted ratio: `{summary['drafted_or_ready_ratio']}`",
        "",
        "## Document Status",
        "",
    ]
    for doc in readiness["documents"]:
        lines.extend(
            [
                f"### {doc['name']}",
                "",
                f"- Status: `{doc['status']}`",
                f"- Artifact found: `{doc['artifact_found']}`",
                f"- Artifact count: `{doc['artifact_count']}` (expected >= `{doc['expected_artifacts']}`)",
                f"- Page limit: `{doc['page_limit']}`",
                f"- Requires admin data: `{doc['requires_admin_data']}`",
                f"- Admin signal present: `{doc['admin_data_signal_present']}`",
                f"- Coverage complete: `{doc['coverage_complete']}`",
                f"- Coverage note: `{doc['coverage_note'] or 'None'}`",
                f"- Blocker: `{doc['blocker_reason'] or 'None'}`",
                f"- Next step: {doc['recommended_next_step']}",
                "",
            ]
        )

    if readiness.get("benchmark_reference"):
        lines.extend(
            [
                "## NSF 26-509 Rigor Benchmark Reference",
                "",
                "This opportunity used the NSF benchmark matrix below as a rigor model:",
                "",
            ]
        )
        for item in readiness["benchmark_reference"]:
            lines.append(
                f"- `{item['name']}` | example status: `{item['status_example']}` | notes: `{item['notes']}`"
            )
    return "\n".join(lines)
