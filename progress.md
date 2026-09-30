# Progress

## 2026-09-29
- settings.json model -> sonnet
- scaffolded folders, git init, .gitignore, CLAUDE.md
- researched datasets; awaiting user pick
- user picked buntyshah/auto-insurance-claims-data (license Unknown, noted); DATA_SOURCES.md; first commit + private repo
- load/clean built; 12 tests pass; ruff clean; data/processed/insurance_claims.parquet (1000x39)
- validate built; 22 tests pass; 6 error rules pass, 2 warns (rows 290 umbrella<0, 578 incident before bind)
