import pytest

from reviewer.checks import build_registry, check_overguarding, run_all
from reviewer.model import ChangeKind, Diff, FileChange, Line, Severity


def change(path, added=(), removed=(), start=1):
    return FileChange(
        path,
        ChangeKind.MODIFIED,
        added=tuple(Line(start + i, text) for i, text in enumerate(added)),
        removed=tuple(Line(start + i, text) for i, text in enumerate(removed)),
    )


def review(*changes, **options):
    return check_overguarding(Diff(files=changes), **options)


def plain(n):
    return [f"const v{i} = {i};" for i in range(n)]


def test_flags_the_overguarded_typescript_file(load_diff):
    findings = check_overguarding(load_diff("overguarded.diff"))
    service = next(f for f in findings if f.path == "src/orders/service.ts")
    assert service.severity is Severity.WARNING
    assert service.check_id == "code-smell/overguarding"
    assert "limit 0.15" in service.message


def test_points_at_the_first_heavy_guard(load_diff):
    service = next(f for f in check_overguarding(load_diff("overguarded.diff")) if f.path == "src/orders/service.ts")
    assert service.line == 14


def test_breakdown_lists_the_most_common_guard_first(load_diff):
    service = next(f for f in check_overguarding(load_diff("overguarded.diff")) if f.path == "src/orders/service.ts")
    breakdown = service.message.split(": ", 1)[1]
    assert breakdown.startswith("4x ?., 3x ??")
    assert "1x swallowed error" in breakdown
    assert "1x ts-ignore" in breakdown


def test_skips_test_files(load_diff):
    assert all(f.path != "src/orders/service.test.ts" for f in check_overguarding(load_diff("overguarded.diff")))


def test_flags_the_python_counterpart(load_diff):
    orders = next(f for f in check_overguarding(load_diff("overguarded.diff")) if f.path == "app/orders.py")
    assert orders.message.startswith("Adds 2 heavy guards in 5 lines")
    assert "swallowed error" in orders.message
    assert "type: ignore" in orders.message
    assert orders.line == 4


def test_density_at_the_limit_does_not_warn():
    lines = ["x?.y;", "a ?? b;", "c?.d;"] + plain(17)
    assert review(change("src/a.ts", lines)) == []
    assert len(review(change("src/a.ts", lines), max_density=0.1)) == 1


def test_density_counts_each_link_of_an_optional_chain():
    findings = review(change("src/a.ts", ["a?.b?.c?.d ?? [];"] + plain(19)))
    assert findings[0].message.startswith("Adds 4 guards in 20 lines (0.20 per line")


def test_guards_removed_by_the_change_are_netted_out():
    added = ["a?.b?.c;", "d ?? e;", "f?.g;"] + plain(17)
    assert len(review(change("src/a.ts", added))) == 1
    assert review(change("src/a.ts", added, removed=["x?.y ?? z;"])) == []


def test_a_large_file_without_guards_is_fine():
    assert review(change("src/a.ts", plain(30)), max_density=-1) == []


def test_small_change_with_only_light_guards_is_fine():
    assert review(change("src/a.ts", ["a?.b ?? c;", "try {"])) == []


def test_small_change_with_a_heavy_guard_warns():
    findings = review(change("src/a.ts", ["const x = y as any;"], start=40))
    assert findings[0].message == "Adds 1 heavy guards in 1 lines: 1x as any."
    assert findings[0].line == 40


def test_small_change_that_only_moves_a_heavy_guard_is_fine():
    assert review(change("src/a.ts", ["const x = z as any;"], removed=["const x = y as any;"])) == []


def test_small_file_threshold_is_configurable():
    assert len(review(change("src/a.ts", ["a?.b;"]), min_lines=1)) == 1


def test_guards_inside_strings_and_comments_are_ignored():
    lines = ['const s = "a?.b ?? c";', "const t = `try {`;", "const u = 'x as any';", "go(); // maybe x?.y"]
    assert review(change("src/a.ts", lines), max_density=0, min_lines=1) == []


def test_escaped_quotes_do_not_end_a_string_early():
    assert review(change("src/a.ts", ['const s = "say \\"a?.b\\" ok";']), max_density=0, min_lines=1) == []


def test_an_escaped_backslash_does_end_a_string():
    assert len(review(change("src/a.ts", ['const s = "\\\\" ?? x;']), max_density=0, min_lines=1)) == 1


def test_multi_line_empty_catch_is_a_swallowed_error():
    findings = review(change("src/a.ts", ["} catch (e) {", "", "}"], start=7))
    assert "1x swallowed error" in findings[0].message
    assert findings[0].line == 7


def test_lines_split_by_a_gap_are_not_joined():
    lines = (Line(3, "} catch (e) {"), Line(9, "}"))
    diff = Diff(files=(FileChange("src/a.ts", ChangeKind.MODIFIED, added=lines),))
    assert check_overguarding(diff) == []


def test_light_guard_line_is_used_when_no_guard_is_heavy():
    findings = review(change("src/a.ts", ["ok();", "a?.b;"], start=10), max_density=0, min_lines=1)
    assert findings[0].line == 11


@pytest.mark.parametrize("path", ["src/a.spec.ts", "src/__tests__/a.ts", "e2e/login.ts", "types/api.d.ts", "README.md"])
def test_non_source_files_are_skipped(path):
    assert review(change(path, ["x as any;"])) == []


@pytest.mark.parametrize("path", ["tests/test_a.py", "app/a_test.py", "conftest.py", "app/test/a.py"])
def test_python_test_files_are_skipped(path):
    assert review(change(path, ["except: pass"])) == []


def test_python_file_named_like_a_test_word_is_still_source():
    assert len(review(change("app/latest_prices.py", ["except: pass"]))) == 1


def test_registry_binds_the_configured_density():
    diff = Diff(files=(change("src/a.ts", ["a?.b;"] + plain(19)),))
    assert run_all(diff, build_registry(max_guard_density=0.01))
    assert run_all(diff, build_registry()) == []


def test_code_before_a_trailing_comment_is_still_scanned():
    findings = review(change("src/a.ts", ["const v = a?.b; // why not"]), max_density=0, min_lines=1)
    assert "1x ?." in findings[0].message


def test_check_list_describes_the_check():
    spec = next(s for s in build_registry() if s.id == "code-smell/overguarding")
    assert spec.severity is Severity.WARNING
    assert spec.summary.startswith("Warns when added lines lean on defensive guards")
