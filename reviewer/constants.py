"""Project-wide constants."""

import re

from reviewer.model import ChangeKind, Severity

DIFF_HEADER = "diff --git "
DEV_NULL = "/dev/null"
HEADER_PATHS = re.compile(r'(?P<old>"(?:[^"\\]|\\.)*"|a/.*?) (?P<new>"(?:[^"\\]|\\.)*"|b/.*)')

CHECK_FILE_COUNT = "diff-size/file-count"
DEFAULT_MAX_FILES = 50

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
