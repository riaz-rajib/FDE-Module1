# FDE Module 1 runnable starter repository

This repository supports **Module 1: Customer Discovery, Stakeholders, Requirements and Value**. It contains only fictional personas, generated facts and local validators.

## Safety boundary

Do not use this repository to contact a real participant, access an external system, collect personal information or test a production service. The structural validator does not approve requirements, accessibility, AI use, privacy, policy, cost or customer value.

## Quick start

```powershell
uv sync --locked
uv run python .\tools\module1.py baseline
uv run python -m unittest discover -s tests -v
uv run python .\tools\module1.py prepare --workspace work\lab1
```

Bash and zsh users replace backslashes with forward slashes.

## Supplied proof

The repository contains exactly 30 public baseline tests. Assessed performance also includes observed discovery, changed constraints and human review. Controlled assessor material is intentionally excluded.
