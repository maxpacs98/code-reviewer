"""Check that added code does not hide behind more defensive guards than it needs."""

from __future__ import annotations

from collections import Counter

from reviewer.constants import (
    CHECK_OVERGUARDING,
    DEFAULT_MAX_GUARD_DENSITY,
    HEAVY_GUARD_WEIGHT,
    LANGUAGES,
    MIN_DENSITY_LINES,
)
from reviewer.model import Diff, FileChange, Finding, GuardPattern, Language, Line, Severity

type Hit = tuple[GuardPattern, int]


def _language_for(path: str, languages: tuple[Language, ...]) -> Language | None:
    """The language a product source file is written in, or None for tests, typings and other files."""
    for language in languages:
        if path.endswith(language.extensions) and not language.non_source.search(path):
            return language
    return None


def _split_comment(text: str, language: Language) -> tuple[str, str]:
    """Separate a line into its code, with string contents blanked, and its trailing comment."""
    code: list[str] = []
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if quote is None:
            if text.startswith(language.line_comment, index):
                return "".join(code), text[index:]
            quote = char if char in language.quotes else None
            code.append(char)
        elif escaped or char == "\\":
            escaped = not escaped
            code.append(" ")
        elif char == quote:
            quote = None
            code.append(char)
        else:
            code.append(" ")
    return "".join(code), ""


def _consecutive_runs(lines: tuple[Line, ...]) -> list[list[Line]]:
    """Group lines into runs whose numbers follow on without a gap."""
    runs: list[list[Line]] = []
    for line in lines:
        if runs and line.number == runs[-1][-1].number + 1:
            runs[-1].append(line)
        else:
            runs.append([line])
    return runs


def _guard_hits(lines: tuple[Line, ...], language: Language) -> list[Hit]:
    """Every guard in the given lines, with the line number it starts on."""
    hits: list[Hit] = []
    for run in _consecutive_runs(lines):
        parts = [_split_comment(line.text, language) for line in run]
        code = "\n".join(part[0] for part in parts)
        comments = "\n".join(part[1] for part in parts)
        for guard in language.guards:
            text = comments if guard.in_comment else code
            hits.extend((guard, run[0].number + text.count("\n", 0, m.start())) for m in guard.pattern.finditer(text))
    return hits


def _weight(hits: list[Hit]) -> int:
    """Total weight of a set of guard hits."""
    return sum(guard.weight for guard, _ in hits)


def _heavy(hits: list[Hit]) -> list[Hit]:
    """Only the hits whose guard is heavy enough to flag on its own."""
    return [hit for hit in hits if hit[0].weight >= HEAVY_GUARD_WEIGHT]


def _finding(change: FileChange, summary: str, hits: list[Hit]) -> Finding:
    """Build the warning for a file, pointing at its first heavy guard, or its first guard when none is heavy."""
    first = min(line for _, line in _heavy(hits) or hits)
    breakdown = ", ".join(f"{count}x {name}" for name, count in Counter(guard.name for guard, _ in hits).most_common())
    return Finding(
        check_id=CHECK_OVERGUARDING,
        severity=Severity.WARNING,
        message=f"{summary}: {breakdown}.",
        path=change.path,
        line=first,
    )


def _review(change: FileChange, language: Language, max_density: float, min_lines: int) -> Finding | None:
    """Score one file's guards, net of the ones it removed, and warn when they go too far."""
    added = _guard_hits(change.added, language)
    removed = _guard_hits(change.removed, language)
    if change.additions >= min_lines:
        density = (_weight(added) - _weight(removed)) / change.additions
        if not added or density <= max_density:
            return None
        summary = (
            f"Adds {len(added)} guards in {change.additions} lines ({density:.2f} per line, limit {max_density:.2f})"
        )
        return _finding(change, summary, added)
    heavy = _heavy(added)
    if _weight(heavy) <= _weight(_heavy(removed)):
        return None
    return _finding(change, f"Adds {len(heavy)} heavy guards in {change.additions} lines", heavy)


def check_overguarding(
    diff: Diff,
    max_density: float = DEFAULT_MAX_GUARD_DENSITY,
    min_lines: int = MIN_DENSITY_LINES,
    languages: tuple[Language, ...] = LANGUAGES,
) -> list[Finding]:
    """Flag files whose added lines lean on defensive guards more than the code seems to need."""
    findings = []
    for change in diff.files:
        language = _language_for(change.path, languages)
        finding = None if language is None else _review(change, language, max_density, min_lines)
        if finding is not None:
            findings.append(finding)
    return findings
