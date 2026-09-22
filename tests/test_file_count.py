import pytest

from reviewer.checks import build_registry, check_file_count, run_all
from reviewer.model import ChangeKind, Diff, FileChange, Severity


def diff_with(n: int) -> Diff:
    return Diff(files=tuple(FileChange(f"src/f{i}.ts", ChangeKind.MODIFIED) for i in range(n)))


@pytest.mark.parametrize("count", [0, 1, 49, 50])
def test_no_finding_at_or_below_the_limit(count):
    assert check_file_count(diff_with(count)) == []


def test_finding_just_above_the_limit():
    findings = check_file_count(diff_with(51))
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert findings[0].check_id == "diff-size/file-count"


def test_message_reports_both_numbers():
    message = check_file_count(diff_with(63))[0].message
    assert "63" in message
    assert "50" in message


def test_limit_is_configurable():
    assert check_file_count(diff_with(5), max_files=10) == []
    assert len(check_file_count(diff_with(5), max_files=4)) == 1


def test_finding_is_not_tied_to_a_file():
    finding = check_file_count(diff_with(51))[0]
    assert finding.path is None
    assert finding.line is None


def test_registry_binds_the_configured_limit():
    assert run_all(diff_with(5), build_registry(max_files=4))
    assert run_all(diff_with(5), build_registry(max_files=10)) == []


def test_registry_specs_have_unique_ids():
    ids = [spec.id for spec in build_registry()]
    assert len(ids) == len(set(ids))
