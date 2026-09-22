"""Terminal rendering of the file table and findings."""

from __future__ import annotations

from collections import defaultdict

from reviewer.constants import BAR_WIDTH, BOLD, CYAN, DIM, GREEN, KIND_COLOR, RED, RESET, SEVERITY_COLOR, SEVERITY_MARK
from reviewer.model import ChangeKind, CheckSpec, Diff, FileChange, Finding


def _paint(text: str, color: str, *, enabled: bool) -> str:
    """Wrap text in an ANSI colour when colour is enabled."""
    return f"{color}{text}{RESET}" if enabled else text


def _display_name(change: FileChange) -> str:
    """Name to show for a file, spelling out both sides of a rename."""
    old_path = change.old_path
    if change.kind is ChangeKind.RENAMED and old_path is not None:
        return f"{old_path} -> {change.path}"
    return change.name


def _bar(change: FileChange, scale: int, *, color: bool) -> str:
    """Proportional +/- bar, scaled against the busiest file in the diff."""
    if change.is_binary or scale <= 0 or change.churn == 0:
        return ""
    width = max(1, round(change.churn / scale * BAR_WIDTH))
    plus = round(width * change.additions / change.churn)
    minus = width - plus
    return _paint("+" * plus, GREEN, enabled=color) + _paint("-" * minus, RED, enabled=color)


def _counts(change: FileChange, *, color: bool) -> str:
    """Right-aligned +/- line counts, or a binary marker."""
    if change.is_binary:
        return _paint("binary".rjust(11), DIM, enabled=color)
    return (
        _paint(f"+{change.additions}".rjust(5), GREEN, enabled=color)
        + " "
        + _paint(f"-{change.deletions}".rjust(5), RED, enabled=color)
    )


def render_file_table(diff: Diff, *, color: bool = False) -> str:
    """Render the changed files, grouped by directory."""
    if not diff.files:
        return "No files changed.\n"

    groups: dict[str, list[FileChange]] = defaultdict(list)
    for change in diff.files:
        groups[change.directory].append(change)

    name_width = max(len(_display_name(c)) for c in diff.files)
    scale = max(c.churn for c in diff.files)

    lines = [_paint(f"Changed files ({len(diff.files)})", BOLD, enabled=color), ""]
    for directory in sorted(groups):
        lines.append(_paint(f"  {directory}/", CYAN, enabled=color))
        for change in sorted(groups[directory], key=lambda c: (-c.churn, c.path)):
            mark = _paint(change.kind.value, KIND_COLOR[change.kind], enabled=color)
            name = _display_name(change).ljust(name_width)
            bar = _bar(change, scale, color=color)
            lines.append(f"    {mark}  {name}  {_counts(change, color=color)}  {bar}".rstrip())
        lines.append("")

    total = _paint(f"+{diff.additions}", GREEN, enabled=color) + " " + _paint(f"-{diff.deletions}", RED, enabled=color)
    lines.append(f"  {len(diff.files)} files changed  {total}")
    return "\n".join(lines) + "\n"


def _location(finding: Finding, *, color: bool) -> str:
    """Dim `path` or `path:line` suffix for a finding, empty when it has neither."""
    if finding.path is None:
        return ""
    where = finding.path if finding.line is None else f"{finding.path}:{finding.line}"
    return _paint(f" {where}", DIM, enabled=color)


def render_findings(findings: list[Finding], *, color: bool = False) -> str:
    """Render the findings produced by the checks."""
    if not findings:
        return "\n" + _paint("No findings.", GREEN, enabled=color) + "\n"

    lines = ["", _paint(f"Findings ({len(findings)})", BOLD, enabled=color), ""]
    for finding in findings:
        mark = _paint(SEVERITY_MARK[finding.severity], SEVERITY_COLOR[finding.severity], enabled=color)
        check = _paint(finding.check_id, DIM, enabled=color)
        lines.append(f"  {mark}  {check}{_location(finding, color=color)}")
        lines.append(f"     {finding.message}")
    return "\n".join(lines) + "\n"


def render_check_list(registry: tuple[CheckSpec, ...], *, color: bool = False) -> str:
    """Render every registered check, one per line."""
    lines = [_paint(f"Checks ({len(registry)})", BOLD, enabled=color), ""]
    width = max(len(spec.id) for spec in registry)
    for spec in registry:
        severity = _paint(spec.severity.value.ljust(7), SEVERITY_COLOR[spec.severity], enabled=color)
        lines.append(f"  {severity}  {spec.id.ljust(width)}  {spec.summary}")
    return "\n".join(lines) + "\n"
