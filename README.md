# code-reviewer

A diff-aware code review CLI. It reads a unified diff, runs checks against it, and prints what it
found. Only changed lines are reviewed, so it stays useful on codebases where a repo-wide linter
would drown you in pre-existing noise.

## Install

```
make venv
```

## Usage

```
.venv/bin/python -m reviewer path/to/change.diff
git diff main... | .venv/bin/python -m reviewer
```

The exit code is `1` when any finding is an error, otherwise `0`, so it drops into CI as-is.

## What it can do

The tool describes itself — these are always current, unlike prose:

```
.venv/bin/python -m reviewer --help          # every option
.venv/bin/python -m reviewer --list-checks   # every check, with severity and what it flags
```

## Development

```
make check      # format, lint, typecheck, test
make mutants    # mutation testing - are the tests actually asserting anything?
```

Tests run against real diff text in `tests/fixtures/*.diff`. Coverage must stay above 95%;
`make test` enforces it.

Conventions for this codebase live in `CLAUDE.md`.
