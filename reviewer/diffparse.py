"""Parser for git-style unified diffs."""

from __future__ import annotations

from reviewer.constants import DEV_NULL, DIFF_HEADER, HEADER_PATHS
from reviewer.model import ChangeKind, Diff, FileChange

_RENAME_FROM = "rename from "
_RENAME_TO = "rename to "
_BINARY_MARKERS = ("Binary files ", "GIT binary patch")


def _unquote(path: str) -> str:
    """Decode a path git wrapped in C-style quotes because of unusual characters."""
    if len(path) < 2 or path[0] != '"' or path[-1] != '"':
        return path
    try:
        # Octal escapes are UTF-8 bytes; latin-1 turns each decoded character back into its byte.
        return path[1:-1].encode().decode("unicode_escape").encode("latin-1").decode("utf-8", errors="replace")
    except UnicodeError:
        return path


def _repo_path(path: str) -> str:
    """Turn a path as written in a diff into a plain repository path."""
    path = _unquote(path)
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


def _header_paths(line: str) -> tuple[str | None, str | None]:
    """Pull the old and new paths out of a `diff --git a/x b/y` line."""
    match = HEADER_PATHS.fullmatch(line[len(DIFF_HEADER) :].strip())
    if match is None:
        return None, None
    return _repo_path(match["old"]), _repo_path(match["new"])


def _split_sections(text: str) -> list[list[str]]:
    """Split diff text into one list of lines per file."""
    sections: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith(DIFF_HEADER):
            current = [line]
            sections.append(current)
        elif current is not None:
            current.append(line)
    return sections


def _parse_section(lines: list[str]) -> FileChange | None:  # noqa: C901, PLR0912
    """Turn one file's worth of diff lines into a `FileChange`."""
    old_path, new_path = _header_paths(lines[0])
    kind = ChangeKind.MODIFIED
    renamed = False
    additions = 0
    deletions = 0
    is_binary = False

    for line in lines[1:]:
        if line.startswith("new file mode"):
            kind = ChangeKind.ADDED
        elif line.startswith("deleted file mode"):
            kind = ChangeKind.DELETED
        elif line.startswith(_RENAME_FROM):
            renamed = True
            old_path = _repo_path(line[len(_RENAME_FROM) :])
        elif line.startswith(_RENAME_TO):
            renamed = True
            new_path = _repo_path(line[len(_RENAME_TO) :])
        elif line.startswith(_BINARY_MARKERS):
            is_binary = True
        elif line.startswith("--- "):
            source = line[4:].strip()
            if source == DEV_NULL:
                kind = ChangeKind.ADDED
            else:
                old_path = _repo_path(source)
        elif line.startswith("+++ "):
            target = line[4:].strip()
            if target == DEV_NULL:
                kind = ChangeKind.DELETED
            else:
                new_path = _repo_path(target)
        elif line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1

    # A deletion has `+++ /dev/null`, so its only real name is the old one.
    path = new_path or old_path
    if path is None:
        return None
    return FileChange(
        path=path,
        kind=ChangeKind.RENAMED if renamed else kind,
        additions=additions,
        deletions=deletions,
        old_path=old_path if (renamed and old_path != path) else None,
        is_binary=is_binary,
    )


def parse_unified_diff(text: str) -> Diff:
    """Parse unified diff text into a `Diff`."""
    parsed = (_parse_section(section) for section in _split_sections(text))
    return Diff(files=tuple(change for change in parsed if change is not None))
