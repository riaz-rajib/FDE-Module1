#!/usr/bin/env sh
set -eu
uv sync --locked
uv run python tools/module1.py baseline
uv run python -m unittest discover -s tests -v
uv run python -m compileall -q tools tests
printf '%s\n' 'Module 1 baseline verification passed.'
