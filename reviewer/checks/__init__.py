"""Registry of every check the reviewer knows about."""

from functools import partial

from reviewer.checks.file_count import check_file_count
from reviewer.checks.overguarding import check_overguarding
from reviewer.constants import CHECK_FILE_COUNT, CHECK_OVERGUARDING, DEFAULT_MAX_FILES, DEFAULT_MAX_GUARD_DENSITY
from reviewer.model import CheckSpec, Diff, Finding, Severity


def build_registry(
    max_files: int = DEFAULT_MAX_FILES, max_guard_density: float = DEFAULT_MAX_GUARD_DENSITY
) -> tuple[CheckSpec, ...]:
    """Every check, with its configuration bound."""
    return (
        CheckSpec(
            id=CHECK_FILE_COUNT,
            severity=Severity.ERROR,
            summary="Flags a diff that touches more files than the limit allows.",
            run=partial(check_file_count, max_files=max_files),
        ),
        CheckSpec(
            id=CHECK_OVERGUARDING,
            severity=Severity.WARNING,
            summary="Warns when added lines lean on defensive guards (?., ??, try, casts, ignores) more than needed.",
            run=partial(check_overguarding, max_density=max_guard_density),
        ),
    )


def run_all(diff: Diff, registry: tuple[CheckSpec, ...]) -> list[Finding]:
    """Run every check in the registry and collect the findings."""
    return [finding for spec in registry for finding in spec.run(diff)]
