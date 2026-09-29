from reviewer.checks import build_registry
from reviewer.model import ChangeKind, Diff, FileChange, Finding, Severity
from reviewer.render import render_check_list, render_file_table, render_findings


def test_table_groups_by_directory(load_diff):
    out = render_file_table(load_diff("mixed.diff"))
    assert "  src/api/" in out
    assert "  assets/" in out
    assert "  ./" in out


def test_table_shows_the_file_count_and_totals(load_diff):
    out = render_file_table(load_diff("mixed.diff"))
    assert "Changed files (6)" in out
    assert "6 files changed  +12 -5" in out


def test_table_marks_renames_with_both_names(load_diff):
    out = render_file_table(load_diff("mixed.diff"))
    assert "src/utils/format.ts -> src/helpers/format.ts" in out


def test_table_labels_binary_files(load_diff):
    out = render_file_table(load_diff("mixed.diff"))
    assert "binary" in out


def test_table_sorts_busiest_file_first_within_a_directory(load_diff):
    out = render_file_table(load_diff("mixed.diff"))
    assert out.index("retry.ts") < out.index("client.ts")


def test_table_handles_an_empty_diff():
    assert render_file_table(Diff()) == "No files changed.\n"


def test_table_is_plain_text_by_default(load_diff):
    assert "\033[" not in render_file_table(load_diff("mixed.diff"))


def test_table_colours_when_asked(load_diff):
    assert "\033[" in render_file_table(load_diff("mixed.diff"), color=True)


def test_bar_is_omitted_for_files_with_no_line_changes():
    diff = Diff(files=(FileChange("a.png", ChangeKind.MODIFIED, is_binary=True),))
    file_line = next(line for line in render_file_table(diff).splitlines() if "a.png" in line)
    assert file_line.endswith("binary")


def test_findings_render_message_and_check_id():
    findings = [Finding("diff-size/file-count", Severity.ERROR, "too many files")]
    out = render_findings(findings)
    assert "diff-size/file-count" in out
    assert "too many files" in out


def test_findings_render_location_when_present():
    findings = [Finding("x/y", Severity.WARNING, "msg", path="src/a.ts", line=12)]
    assert "src/a.ts:12" in render_findings(findings)


def test_no_findings_message():
    assert "No findings." in render_findings([])


def test_check_list_shows_id_severity_and_summary():
    out = render_check_list(build_registry())
    assert f"Checks ({len(build_registry())})" in out
    assert "diff-size/file-count" in out
    assert "error" in out
    assert "limit" in out


def test_check_list_colours_when_asked():
    assert "\033[" in render_check_list(build_registry(), color=True)
