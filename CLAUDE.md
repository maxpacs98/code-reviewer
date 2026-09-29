# code-reviewer

A diff-aware code review CLI. Reads a unified diff, runs checks, prints findings.

## Rules

1. **Coverage.** Every change keeps coverage above 95%. `make test` enforces it; do not lower the threshold to make a change pass. Coverage says a line ran, not that a test checks it - `make mutants` is what tells you whether the tests would catch a regression.
2. **Constants.** All constants live in `reviewer/constants.py`. Never define them at the top of a module.
3. **Docstrings.** Every module, class and non-trivial function gets a docstring of **exactly one line**. It says what the thing is for, not how it works.
4. **Almost no comments.** Code explains itself through naming and structure. The only comment worth writing is one that explains something genuinely non-obvious that naming cannot carry - a quirk of an external format, a subtle invariant. If a comment restates the code, delete it.
5. **Reuse first.** Before writing anything new, look for an existing implementation. If it almost fits, refactor it so both callers share it — with tests proving no regression — rather than writing a second version.

## Modules

- **Ask before adding a package.** 
- No `utils.py`, `helpers.py` or `common.py`. A module is named for the concept it owns.
- A helper stays private in the module that uses it until a *second* module needs it. When it moves,
  it moves to the module owning that concept - or onto the data model, when it is derived from that data.
- Split a module when it has two responsibilities, not when it hits a line count. `render.py` becomes a
  `render/` package split by output target, never `render_utils.py`.
- Imports flow one way. `model.py` imports nothing from the project; `constants.py` imports only `model`;
  parsing, checks and rendering import from those but never from each other's layer or from `cli`; `cli` sits
  on top and may import anything. Never introduce a cycle.

## Layout

- `reviewer/model.py` — frozen dataclasses: `Diff`, `FileChange`, `Finding`.
- `reviewer/diffparse.py` — hand-rolled unified diff parser. No third-party diff library.
- `reviewer/checks/` — one module per check, pure functions `Diff -> list[Finding]`. No I/O. `__init__.py` is the registry: a new check is added there so `--list-checks` and the README stay current for free.
- `reviewer/render.py` — terminal output. All ANSI colour lives here.
- `reviewer/cli.py` — argument parsing and the only place that touches stdin/stdout.
- `tests/fixtures/*.diff` — real diff text. Prefer adding a fixture over building a `Diff` by hand when testing the parser or renderer.

Checks stay pure so they are trivially testable; I/O stays at the edges.

## Formatting

`ruff format` at 120 columns with `skip-magic-trailing-comma = true`. Line breaks are decided by
width alone, so code stays horizontal until it genuinely does not fit.

## Running it

Run `make check` before finishing a change. It formats, lints, typechecks and tests.
There is no activated virtualenv, so every tool needs its `.venv/bin/` prefix - use the Makefile.

## Tone

Playful and critical humour in chat is welcome. Never in code, comments, commits or docs.

## Changing these rules

This file is not yours to edit, and it should change rarely. If a rule blocks the correct change, or
something here has become false, stop and say so. Do not work around it, and do not quietly update
this file. The one exception: when I have approved a new package, add its line to **Layout** as part
of that change.
