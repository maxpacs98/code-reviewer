"""Check that a merge request does not touch too many files."""

from __future__ import annotations

from reviewer.constants import CHECK_FILE_COUNT, DEFAULT_MAX_FILES
from reviewer.model import Diff, Finding, Severity


def check_file_count(diff: Diff, max_files: int = DEFAULT_MAX_FILES) -> list[Finding]:
    """Flag diffs that touch more files than the limit allows."""
    count = len(diff.files)
    if count <= max_files:
        return []
    return [
        Finding(
            check_id=CHECK_FILE_COUNT,
            severity=Severity.ERROR,
            message=(
                f"{count} files changed, limit is {max_files}. Consider splitting this into smaller merge requests."
            ),
        )
    ]
