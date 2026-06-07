"""CLI entrypoint for Grant Applier."""

from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import analyze_opportunity
from .budget import generate_budget
from .discovery import discover_opportunities
from .drafting import generate_drafts
from .inventory import build_inventory, inventory_json, inventory_text_table, resolve_opportunity
from .profiles import ensure_profile
from .requirement_extractor import extract_requirements
from .source_discovery import run_source_discovery
from .validation import validate_opportunity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grant-applier",
        description="Grant opportunity inventory and analysis scaffolding CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Scan applicant folders and list available opportunities.",
    )
    inventory_parser.add_argument(
        "--root",
        default=".",
        help="Repository root path (default: current directory).",
    )
    inventory_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format.",
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Generate opportunity analysis skeleton files.",
    )
    analyze_parser.add_argument(
        "opportunity",
        nargs="?",
        help='Opportunity path, e.g. "SGDI/NSF 26-508".',
    )
    analyze_parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all discovered opportunities.",
    )
    analyze_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite previously generated scaffold files.",
    )
    analyze_parser.add_argument(
        "--root",
        default=".",
        help="Repository root path (default: current directory).",
    )

    research_parser = subparsers.add_parser(
        "research",
        help="Discover official/candidate sources and update source index.",
    )
    configure_target_arguments(research_parser)
    research_parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live web discovery and only write seed candidate links.",
    )

    requirements_parser = subparsers.add_parser(
        "requirements",
        help="Extract requirements and create structured requirement artifacts.",
    )
    configure_target_arguments(requirements_parser)

    draft_parser = subparsers.add_parser(
        "draft",
        help="Generate draft narrative markdown files.",
    )
    configure_target_arguments(draft_parser)

    budget_parser = subparsers.add_parser(
        "budget",
        help="Generate budget workbooks and assumptions.",
    )
    configure_target_arguments(budget_parser)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate generated artifacts and create compliance report.",
    )
    configure_target_arguments(validate_parser)

    build_parser = subparsers.add_parser(
        "build",
        help="Run full pipeline: analyze -> research -> requirements -> draft -> budget -> validate.",
    )
    configure_target_arguments(build_parser)
    build_parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live web discovery during full pipeline.",
    )

    return parser


def configure_target_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "opportunity",
        nargs="?",
        help='Opportunity path, e.g. "SGDI/NSF 26-508".',
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run command for all discovered opportunities.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite previously generated files where applicable.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root path (default: current directory).",
    )


def run_inventory(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    items = build_inventory(root)
    if args.format == "json":
        print(inventory_json(items))
    else:
        print(inventory_text_table(items))
    return 0


def run_analyze(args: argparse.Namespace) -> int:
    opportunities = resolve_targets(args)

    for opportunity in opportunities:
        analyze_opportunity(opportunity, overwrite=args.overwrite)
        ensure_profile(opportunity, overwrite=False)
        print(f"Analyzed: {opportunity.relative_id}")
    return 0


def run_research(args: argparse.Namespace) -> int:
    opportunities = resolve_targets(args)
    for opportunity in opportunities:
        run_source_discovery(
            opportunity=opportunity,
            overwrite=args.overwrite,
            online=not args.offline,
        )
        print(f"Researched: {opportunity.relative_id}")
    return 0


def run_requirements(args: argparse.Namespace) -> int:
    opportunities = resolve_targets(args)
    for opportunity in opportunities:
        extract_requirements(opportunity=opportunity, overwrite=args.overwrite)
        print(f"Requirements extracted: {opportunity.relative_id}")
    return 0


def run_draft(args: argparse.Namespace) -> int:
    opportunities = resolve_targets(args)
    for opportunity in opportunities:
        created = generate_drafts(opportunity=opportunity, overwrite=args.overwrite)
        print(f"Drafted: {opportunity.relative_id} ({len(created)} files)")
    return 0


def run_budget(args: argparse.Namespace) -> int:
    opportunities = resolve_targets(args)
    for opportunity in opportunities:
        created = generate_budget(opportunity=opportunity, overwrite=args.overwrite)
        print(f"Budget generated: {opportunity.relative_id} ({len(created)} files)")
    return 0


def run_validate(args: argparse.Namespace) -> int:
    opportunities = resolve_targets(args)
    for opportunity in opportunities:
        report = validate_opportunity(opportunity=opportunity, overwrite=True)
        missing = len(report.get("missing_items", []))
        print(f"Validated: {opportunity.relative_id} (missing items: {missing})")
    return 0


def run_build(args: argparse.Namespace) -> int:
    opportunities = resolve_targets(args)
    for opportunity in opportunities:
        analyze_opportunity(opportunity, overwrite=args.overwrite)
        ensure_profile(opportunity, overwrite=False)
        run_source_discovery(opportunity, overwrite=args.overwrite, online=not args.offline)
        extract_requirements(opportunity, overwrite=args.overwrite)
        generate_drafts(opportunity, overwrite=args.overwrite)
        generate_budget(opportunity, overwrite=args.overwrite)
        validate_opportunity(opportunity, overwrite=True)
        print(f"Built full package: {opportunity.relative_id}")
    return 0


def resolve_targets(args: argparse.Namespace):
    root = Path(args.root).resolve()
    if args.all:
        return discover_opportunities(root)
    if not args.opportunity:
        raise ValueError('Provide an opportunity like "SGDI/NSF 26-508" or use --all.')
    return [resolve_opportunity(root, args.opportunity)]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            return run_inventory(args)
        if args.command == "analyze":
            return run_analyze(args)
        if args.command == "research":
            return run_research(args)
        if args.command == "requirements":
            return run_requirements(args)
        if args.command == "draft":
            return run_draft(args)
        if args.command == "budget":
            return run_budget(args)
        if args.command == "validate":
            return run_validate(args)
        if args.command == "build":
            return run_build(args)
    except ValueError as error:
        parser.error(str(error))
    return 1
