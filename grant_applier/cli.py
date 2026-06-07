"""CLI entrypoint for Grant Applier."""

from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import analyze_opportunity
from .discovery import discover_opportunities
from .inventory import build_inventory, inventory_json, inventory_text_table, resolve_opportunity


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

    return parser


def run_inventory(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    items = build_inventory(root)
    if args.format == "json":
        print(inventory_json(items))
    else:
        print(inventory_text_table(items))
    return 0


def run_analyze(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if args.all:
        opportunities = discover_opportunities(root)
    else:
        if not args.opportunity:
            raise ValueError('Provide an opportunity like "SGDI/NSF 26-508" or use --all.')
        opportunities = [resolve_opportunity(root, args.opportunity)]

    for opportunity in opportunities:
        analyze_opportunity(opportunity, overwrite=args.overwrite)
        print(f"Analyzed: {opportunity.relative_id}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            return run_inventory(args)
        if args.command == "analyze":
            return run_analyze(args)
    except ValueError as error:
        parser.error(str(error))
    return 1
