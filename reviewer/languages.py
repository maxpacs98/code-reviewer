"""The languages the reviewer can read, and how to read source text written in each."""

from __future__ import annotations

import re

from reviewer.constants import HEAVY_GUARD_WEIGHT
from reviewer.model import GuardPattern, Language

TYPESCRIPT = Language(
    name="TypeScript",
    extensions=(".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"),
    non_source=re.compile(r"\.(?:test|spec|stories)\.|(?:^|/)(?:__tests__|e2e)/|\.d\.ts$"),
    line_comment="//",
    quotes=("'", '"', "`"),
    guards=(
        GuardPattern("?.", re.compile(r"\?\.(?!\d)"), example="a?.b"),
        GuardPattern("??", re.compile(r"\?\?"), example="a ?? b"),
        GuardPattern("try", re.compile(r"\btry\s*\{"), example="try {"),
        GuardPattern(
            "nullish check",
            re.compile(r"[!=]==?\s*(?:undefined|null)\b|\b(?:undefined|null)\s*[!=]==?"),
            example="if (x === undefined) go();",
        ),
        GuardPattern(
            "typeof check", re.compile(r"\btypeof\s+[\w.$?]+\s*[!=]==?"), example="if (typeof x?.y === 'number') go();"
        ),
        GuardPattern(
            "early bail-out",
            re.compile(r"\bif\s*\(\s*!\s*[\w.$?]+\s*\)\s*\{?\s*(?:return|throw)\b"),
            example="if (!user) return;",
        ),
        GuardPattern(
            "|| fallback", re.compile(r"\|\|\s*(?:\[\s*\]|\{\s*\}|([\"'`])\1|0\b)"), example="const xs = ys || [];"
        ),
        GuardPattern(
            "swallowed error",
            re.compile(
                r"\bcatch\s*(?:\([^)]*\))?\s*\{\s*\}|\.catch\(\s*(?:\([^)]*\)|\w+)\s*=>\s*(?:\{\s*\}|undefined|null)\s*\)"
            ),
            weight=HEAVY_GUARD_WEIGHT,
            example="p.catch(() => {});",
        ),
        GuardPattern(
            "as any",
            re.compile(r"\bas\s+(?:any\b|unknown\s+as\b)"),
            weight=HEAVY_GUARD_WEIGHT,
            example="const x = y as any;",
        ),
        GuardPattern(
            "ts-ignore",
            re.compile(r"@ts-(?:ignore|expect-error|nocheck)\b"),
            weight=HEAVY_GUARD_WEIGHT,
            in_comment=True,
            example="// @ts-ignore",
        ),
    ),
)

PYTHON = Language(
    name="Python",
    extensions=(".py",),
    non_source=re.compile(r"(?:^|/)(?:test_[^/]*|[^/]*_test\.py|conftest\.py)$|(?:^|/)tests?/"),
    line_comment="#",
    quotes=("'", '"'),
    guards=(
        GuardPattern("try", re.compile(r"\btry\s*:"), example="try:"),
        GuardPattern(
            "broad except",
            re.compile(r"\bexcept\s*(?:\(?\s*(?:Base)?Exception\b[^:]*)?:"),
            example="except Exception as e:",
        ),
        GuardPattern("None check", re.compile(r"\bis\s+(?:not\s+)?None\b"), example="if x is not None:"),
        GuardPattern(
            "early bail-out", re.compile(r"\bif\s+not\s+[\w.]+\s*:\s*(?:return|raise)\b"), example="if not user: return"
        ),
        GuardPattern(
            "getattr default", re.compile(r"\bgetattr\([^()]*,[^()]*,[^()]*\)"), example="v = getattr(x, 'y', None)"
        ),
        GuardPattern("hasattr", re.compile(r"\bhasattr\("), example="if hasattr(x, 'y'):"),
        GuardPattern(
            "or fallback", re.compile(r"\bor\s+(?:\[\s*\]|\{\s*\}|([\"'])\1|0\b|None\b)"), example="xs = ys or []"
        ),
        GuardPattern(
            "swallowed error",
            re.compile(r"\bexcept\b[^:\n]*:\s*(?:pass\b|\.\.\.)"),
            weight=HEAVY_GUARD_WEIGHT,
            example="except ValueError: pass",
        ),
        GuardPattern(
            "cast Any", re.compile(r"\bcast\(\s*Any\b"), weight=HEAVY_GUARD_WEIGHT, example="v = cast(Any, x)"
        ),
        GuardPattern(
            "type: ignore",
            re.compile(r"\b(?:type|pyright):\s*ignore\b"),
            weight=HEAVY_GUARD_WEIGHT,
            in_comment=True,
            example="v = x  # type: ignore",
        ),
    ),
)

LANGUAGES = (TYPESCRIPT, PYTHON)


def language_for(path: str, languages: tuple[Language, ...] = LANGUAGES) -> Language | None:
    """The language a product source file is written in, or None for tests, typings and other files."""
    for language in languages:
        if path.endswith(language.extensions) and not language.non_source.search(path):
            return language
    return None


def split_comment(text: str, language: Language) -> tuple[str, str]:
    """Separate a line into its code, with string contents blanked, and its trailing comment."""
    code: list[str] = []
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if quote is None:
            if text.startswith(language.line_comment, index):
                return "".join(code), text[index:]
            quote = char if char in language.quotes else None
            code.append(char)
        elif escaped or char == "\\":
            escaped = not escaped
            code.append(" ")
        elif char == quote:
            quote = None
            code.append(char)
        else:
            code.append(" ")
    return "".join(code), ""
