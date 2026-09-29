import pytest

from reviewer.languages import PYTHON, TYPESCRIPT, language_for, split_comment


@pytest.mark.parametrize(
    ("path", "language"),
    [("src/a.ts", TYPESCRIPT), ("src/A.tsx", TYPESCRIPT), ("lib/a.mjs", TYPESCRIPT), ("app/a.py", PYTHON)],
)
def test_source_files_map_to_their_language(path, language):
    assert language_for(path) is language


@pytest.mark.parametrize("path", ["README.md", "src/a.test.ts", "types/a.d.ts", "tests/test_a.py", "assets/a.png"])
def test_other_files_have_no_language(path):
    assert language_for(path) is None


def test_split_comment_blanks_strings_and_separates_the_comment():
    assert split_comment('x = "a // b"  // note', TYPESCRIPT) == ('x = "      "  ', "// note")


def test_split_comment_uses_the_languages_comment_marker():
    assert split_comment("x = 1  # note // not ts", PYTHON) == ("x = 1  ", "# note // not ts")


def test_split_comment_without_a_comment():
    assert split_comment("return 'it\\'s';", TYPESCRIPT) == ("return '     ';", "")
