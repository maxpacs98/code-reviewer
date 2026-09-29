"""Command line entry point."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from reviewer.checks import build_registry, run_all
from reviewer.constants import DEFAULT_MAX_FILES, DEFAULT_MAX_GUARD_DENSITY, EXIT_FINDINGS, EXIT_OK
from reviewer.diffparse import parse_unified_diff
from reviewer.model import Finding, Severity
from reviewer.render import render_check_list, render_file_table, render_findings


def _build_parser() -> argparse.ArgumentParser:
    """Define the command line interface."""
    parser = argparse.ArgumentParser(prog="reviewer", description="Review a unified diff.")
    parser.add_argument(
        "diff", nargs="?", default="-", help="path to a unified diff file, or - to read stdin (default: -)"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=DEFAULT_MAX_FILES,
        help=f"fail above this many changed files (default: {DEFAULT_MAX_FILES})",
    )
    parser.add_argument(
        "--max-guard-density",
        type=float,
        default=DEFAULT_MAX_GUARD_DENSITY,
        help=f"warn above this many weighted guards per added line (default: {DEFAULT_MAX_GUARD_DENSITY})",
    )
    parser.add_argument("--list-checks", action="store_true", help="list every available check and exit")
    parser.add_argument("--no-color", action="store_true", help="disable coloured output")
    return parser


def _read_diff(source: str) -> str:
    """Read diff text from a path, or from stdin when the source is `-`."""
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8", errors="replace")


def _use_color(*, no_color_flag: bool) -> bool:
    """Decide whether to emit ANSI colour."""
    if no_color_flag or os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def main(argv: list[str] | None = None) -> int:
    """Run the reviewer and return the process exit code."""
    args = _build_parser().parse_args(argv)
    color = _use_color(no_color_flag=args.no_color)

    registry = build_registry(max_files=args.max_files, max_guard_density=args.max_guard_density)
    if args.list_checks:
        sys.stdout.write(render_check_list(registry, color=color))
        return EXIT_OK

    diff = parse_unified_diff(_read_diff(args.diff))
    findings: list[Finding] = run_all(diff, registry)

    sys.stdout.write(render_file_table(diff, color=color))
    sys.stdout.write(render_findings(findings, color=color))

    blocking = any(f.severity is Severity.ERROR for f in findings)
    return EXIT_FINDINGS if blocking else EXIT_OK
