#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

if "${PYTHON_BIN}" -c "import setuptools" >/dev/null 2>&1; then
  "${PYTHON_BIN}" -m pip install -e '.[dev]'
else
  echo "setuptools unavailable; using src layout without editable install" >&2
  export PYTHONPATH="${PWD}/src${PYTHONPATH:+:${PYTHONPATH}}"
fi

"${PYTHON_BIN}" -m pytest -q
