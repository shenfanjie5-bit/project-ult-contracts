PYTHON ?= python3
PYTHONPATH ?= src
export PYTHONPATH

.PHONY: install test test-fast smoke lint typecheck ci

install:
	$(PYTHON) -m pip install -e ".[dev]"

# Full test suite — legacy tests at tests/*.py + new canonical tier dirs
# (tests/unit, tests/boundary, tests/smoke, tests/regression).
test:
	$(PYTHON) -m pytest

# Fast lane for PR CI and local pre-commit. unit + boundary only.
test-fast:
	$(PYTHON) -m pytest tests/unit tests/boundary -q

# Minimal smoke — exercises public entrypoints. Infra-free.
smoke:
	$(PYTHON) -m pytest tests/smoke -q

lint:
	$(PYTHON) -m ruff check . || true

typecheck:
	$(PYTHON) -m mypy src tests || true

ci: test
