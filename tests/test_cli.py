from pathlib import Path

from reviewer.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_exits_zero_on_a_clean_diff(capsys):
    assert main([str(FIXTURES / "mixed.diff"), "--no-color"]) == 0
    assert "Changed files (6)" in capsys.readouterr().out


def test_exits_one_when_the_file_limit_is_exceeded(capsys):
    assert main([str(FIXTURES / "mixed.diff"), "--max-files", "2", "--no-color"]) == 1
    assert "diff-size/file-count" in capsys.readouterr().out


def test_reads_stdin_by_default(monkeypatch, capsys):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO((FIXTURES / "mixed.diff").read_text()))
    assert main(["--no-color"]) == 0
    assert "Changed files (6)" in capsys.readouterr().out


def test_list_checks_exits_zero_without_reading_a_diff(capsys):
    assert main(["--list-checks", "--no-color"]) == 0
    assert "diff-size/file-count" in capsys.readouterr().out


def test_overguarding_warns_without_failing_the_run(capsys):
    assert main([str(FIXTURES / "overguarded.diff"), "--no-color"]) == 0
    assert "code-smell/overguarding" in capsys.readouterr().out


def test_guard_density_limit_is_a_flag(capsys):
    main([str(FIXTURES / "overguarded.diff"), "--max-guard-density", "5", "--no-color"])
    assert "src/orders/service.ts" not in capsys.readouterr().out.split("Findings")[-1]
