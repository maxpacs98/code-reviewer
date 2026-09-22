"""Registry of every check the reviewer knows about."""

from functools import partial

from reviewer.checks.file_count import check_file_count
from reviewer.constants import CHECK_FILE_COUNT, DEFAULT_MAX_FILES
from reviewer.model import CheckSpec, Diff, Finding, Severity


def build_registry(max_files: int = DEFAULT_MAX_FILES) -> tuple[CheckSpec, ...]:
    """Every check, with its configuration bound."""
    return (
        CheckSpec(
            id=CHECK_FILE_COUNT,
            severity=Severity.ERROR,
            summary="Flags a diff that touches more files than the limit allows.",
            run=partial(check_file_count, max_files=max_files),
        ),
    )


def run_all(diff: Diff, registry: tuple[CheckSpec, ...]) -> list[Finding]:
    """Run every check in the registry and collect the findings."""
    return [finding for spec in registry for finding in spec.run(diff)]
