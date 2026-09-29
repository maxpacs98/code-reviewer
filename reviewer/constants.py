"""Project-wide constants."""

import re

from reviewer.model import ChangeKind, GuardPattern, Language, Severity

DIFF_HEADER = "diff --git "
DEV_NULL = "/dev/null"
HEADER_PATHS = re.compile(r'(?P<old>"(?:[^"\\]|\\.)*"|a/.*?) (?P<new>"(?:[^"\\]|\\.)*"|b/.*)')
HUNK_HEADER = re.compile(r"@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@")
RENAME_FROM = "rename from "
RENAME_TO = "rename to "
BINARY_MARKERS = ("Binary files ", "GIT binary patch")

CHECK_FILE_COUNT = "diff-size/file-count"
DEFAULT_MAX_FILES = 50

CHECK_OVERGUARDING = "code-smell/overguarding"
DEFAULT_MAX_GUARD_DENSITY = 0.15
MIN_DENSITY_LINES = 20
HEAVY_GUARD_WEIGHT = 3

TYPESCRIPT = Language(
    name="TypeScript",
    extensions=(".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"),
    non_source=re.compile(r"\.(?:test|spec|stories)\.|(?:^|/)(?:__tests__|e2e)/|\.d\.ts$"),
    line_comment="//",
    quotes=("'", '"', "`"),
    guards=(
        GuardPattern("?.", re.compile(r"\?\.(?!\d)")),
        GuardPattern("??", re.compile(r"\?\?")),
        GuardPattern("try", re.compile(r"\btry\s*\{")),
        GuardPattern("nullish check", re.compile(r"[!=]==?\s*(?:undefined|null)\b|\b(?:undefined|null)\s*[!=]==?")),
        GuardPattern("typeof check", re.compile(r"\btypeof\s+[\w.$?]+\s*[!=]==?")),
        GuardPattern("early bail-out", re.compile(r"\bif\s*\(\s*!\s*[\w.$?]+\s*\)\s*\{?\s*(?:return|throw)\b")),
        GuardPattern("|| fallback", re.compile(r"\|\|\s*(?:\[\s*\]|\{\s*\}|([\"'`])\1|0\b)")),
        GuardPattern(
            "swallowed error",
            re.compile(
                r"\bcatch\s*(?:\([^)]*\))?\s*\{\s*\}|\.catch\(\s*(?:\([^)]*\)|\w+)\s*=>\s*(?:\{\s*\}|undefined|null)\s*\)"
            ),
            weight=HEAVY_GUARD_WEIGHT,
        ),
        GuardPattern("as any", re.compile(r"\bas\s+(?:any\b|unknown\s+as\b)"), weight=HEAVY_GUARD_WEIGHT),
        GuardPattern(
            "ts-ignore",
            re.compile(r"@ts-(?:ignore|expect-error|nocheck)\b"),
            weight=HEAVY_GUARD_WEIGHT,
            in_comment=True,
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
        GuardPattern("try", re.compile(r"\btry\s*:")),
        GuardPattern("broad except", re.compile(r"\bexcept\s*(?:\(?\s*(?:Base)?Exception\b[^:]*)?:")),
        GuardPattern("None check", re.compile(r"\bis\s+(?:not\s+)?None\b")),
        GuardPattern("early bail-out", re.compile(r"\bif\s+not\s+[\w.]+\s*:\s*(?:return|raise)\b")),
        GuardPattern("getattr default", re.compile(r"\bgetattr\([^()]*,[^()]*,[^()]*\)")),
        GuardPattern("hasattr", re.compile(r"\bhasattr\(")),
        GuardPattern("or fallback", re.compile(r"\bor\s+(?:\[\s*\]|\{\s*\}|([\"'])\1|0\b|None\b)")),
        GuardPattern(
            "swallowed error", re.compile(r"\bexcept\b[^:\n]*:\s*(?:pass\b|\.\.\.)"), weight=HEAVY_GUARD_WEIGHT
        ),
        GuardPattern("cast Any", re.compile(r"\bcast\(\s*Any\b"), weight=HEAVY_GUARD_WEIGHT),
        GuardPattern(
            "type: ignore", re.compile(r"\b(?:type|pyright):\s*ignore\b"), weight=HEAVY_GUARD_WEIGHT, in_comment=True
        ),
    ),
)

LANGUAGES = (TYPESCRIPT, PYTHON)

BAR_WIDTH = 20
RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"

KIND_COLOR = {ChangeKind.ADDED: GREEN, ChangeKind.MODIFIED: YELLOW, ChangeKind.DELETED: RED, ChangeKind.RENAMED: BLUE}

SEVERITY_COLOR = {Severity.ERROR: RED, Severity.WARNING: YELLOW, Severity.INFO: CYAN}

SEVERITY_MARK = {Severity.ERROR: "x", Severity.WARNING: "!", Severity.INFO: "i"}

EXIT_OK = 0
EXIT_FINDINGS = 1
