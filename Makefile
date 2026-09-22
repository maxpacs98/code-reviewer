VENV := .venv
PY := $(VENV)/bin/python
BIN := $(VENV)/bin

.PHONY: venv test lint types fmt check run mutants

venv:
	python3 -m venv $(VENV)
	$(BIN)/pip install -q -r requirements-dev.txt

test:
	$(PY) -m pytest --cov=reviewer --cov-report=term-missing --cov-fail-under=95

lint:
	$(BIN)/ruff check .

types:
	$(BIN)/ty check .

fmt:
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

check: fmt lint types test

run:
	$(PY) -m reviewer $(ARGS)

mutants:
	$(BIN)/mutmut run
	$(BIN)/mutmut results
