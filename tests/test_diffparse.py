from reviewer.diffparse import parse_unified_diff
from reviewer.model import ChangeKind


def test_parses_every_file_in_the_fixture(load_diff):
    diff = load_diff("mixed.diff")
    assert [f.path for f in diff.files] == [
        "src/api/client.ts",
        "src/api/retry.ts",
        "src/legacy/poller.ts",
        "src/helpers/format.ts",
        "assets/logo.png",
        "README.md",
    ]


def test_classifies_change_kinds(load_diff):
    diff = load_diff("mixed.diff")
    kinds = {f.path: f.kind for f in diff.files}
    assert kinds["src/api/client.ts"] is ChangeKind.MODIFIED
    assert kinds["src/api/retry.ts"] is ChangeKind.ADDED
    assert kinds["src/legacy/poller.ts"] is ChangeKind.DELETED
    assert kinds["src/helpers/format.ts"] is ChangeKind.RENAMED


def test_rename_keeps_the_old_path(load_diff):
    diff = load_diff("mixed.diff")
    renamed = next(f for f in diff.files if f.kind is ChangeKind.RENAMED)
    assert renamed.old_path == "src/utils/format.ts"


def test_non_renames_have_no_old_path(load_diff):
    diff = load_diff("mixed.diff")
    assert all(f.old_path is None for f in diff.files if f.kind is not ChangeKind.RENAMED)


def test_counts_added_and_removed_lines(load_diff):
    diff = load_diff("mixed.diff")
    counts = {f.path: (f.additions, f.deletions) for f in diff.files}
    assert counts["src/api/client.ts"] == (3, 1)
    assert counts["src/api/retry.ts"] == (7, 0)
    assert counts["src/legacy/poller.ts"] == (0, 3)
    assert counts["README.md"] == (1, 0)
    assert counts["src/helpers/format.ts"] == (1, 1)


def test_hunk_headers_are_not_counted_as_changed_lines(load_diff):
    diff = load_diff("mixed.diff")
    retry = next(f for f in diff.files if f.path == "src/api/retry.ts")
    assert retry.deletions == 0


def test_detects_binary_files(load_diff):
    diff = load_diff("mixed.diff")
    logo = next(f for f in diff.files if f.path == "assets/logo.png")
    assert logo.is_binary
    assert logo.churn == 0


def test_totals(load_diff):
    diff = load_diff("mixed.diff")
    assert diff.additions == 12
    assert diff.deletions == 5


def test_empty_diff_yields_no_files(load_diff):
    assert load_diff("empty.diff").files == ()


def test_garbage_input_does_not_raise():
    assert parse_unified_diff("not a diff at all\n@@ -1 +1 @@\n").files == ()


def test_directory_of_a_root_level_file(load_diff):
    diff = load_diff("mixed.diff")
    readme = next(f for f in diff.files if f.path == "README.md")
    assert readme.directory == "."
