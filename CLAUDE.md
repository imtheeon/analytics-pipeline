# analytics-pipeline

## Goal
A simple, reusable pipeline: **load → clean → validate → store (DuckDB) → analyze (SQL) → report**.
Generic steps live in `core/`; industry-specific logic in `industries/<name>/` (first: insurance).
Raw files go in `data/inbox/`, cleaned output in `data/processed/`, results in `reports/`.

## Rules
- Always use the conda environment `data-analysis` (`conda run -n data-analysis ...`).
- Use pandas 3.0 syntax (Copy-on-Write, default string dtype). Check context7 when unsure.
- Use the data plugin skills at each step (e.g. explore-data, write-query/sql-queries, statistical-analysis, create-viz).
- Run `validate-data` before reporting any results.
- Write a pytest test for each step in `tests/`.
- Run `ruff check` and `ruff format` before committing.
