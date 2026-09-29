"""Domain model for a parsed diff and the findings checks produce."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ChangeKind(Enum):
    """How a file was touched by the diff."""

    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"


@dataclass(frozen=True)
class Line:
    """One added or removed line, numbered as it appears in its side of the file."""

    number: int
    text: str


@dataclass(frozen=True)
class FileChange:
    """A single file touched by a diff."""

    path: str
    kind: ChangeKind
    added: tuple[Line, ...] = ()
    removed: tuple[Line, ...] = ()
    old_path: str | None = None
    is_binary: bool = False

    @property
    def additions(self) -> int:
        return len(self.added)

    @property
    def deletions(self) -> int:
        return len(self.removed)

    @property
    def churn(self) -> int:
        """Total lines touched, used for sorting and for the size bar."""
        return self.additions + self.deletions

    @property
    def name(self) -> str:
        """File name without its directory."""
        _, sep, tail = self.path.rpartition("/")
        return tail if sep else self.path

    @property
    def directory(self) -> str:
        """Directory the file lives in, or '.' for repository-root files."""
        head, sep, _ = self.path.rpartition("/")
        return head if sep else "."


@dataclass(frozen=True)
class Diff:
    """A parsed unified diff."""

    files: tuple[FileChange, ...] = ()

    @property
    def additions(self) -> int:
        return sum(f.additions for f in self.files)

    @property
    def deletions(self) -> int:
        return sum(f.deletions for f in self.files)


class Severity(Enum):
    """How much a finding should block a merge."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    """Something a check wants the reviewer to know about."""

    check_id: str
    severity: Severity
    message: str
    path: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class CheckSpec:
    """A check's identity, plus the configured function that runs it."""

    id: str
    severity: Severity
    summary: str
    run: Callable[[Diff], list[Finding]]


@dataclass(frozen=True)
class GuardPattern:
    """A defensive construct worth counting, and how much it weighs against the code that uses it."""

    name: str
    pattern: re.Pattern[str]
    weight: int = 1
    in_comment: bool = False


@dataclass(frozen=True)
class Language:
    """What the reviewer needs to know to read source files written in one language."""

    name: str
    extensions: tuple[str, ...]
    non_source: re.Pattern[str]
    line_comment: str
    quotes: tuple[str, ...]
    guards: tuple[GuardPattern, ...]
