# Task: analytics-pipeline project setup

## Goal
Scaffold project, pick an insurance claims dataset, push to a private GitHub repo.

## Next Step
Next: validate step (flag umbrella_limit < 0, claim parts sum), then store in DuckDB.

### Phase 1: settings.json model opusplan → sonnet
**Status:** complete
### Phase 2: folders, git init, .gitignore, CLAUDE.md
**Status:** complete
### Phase 3: research 3 Kaggle claims datasets (see findings.md)
**Status:** complete
### Phase 4: DATA_SOURCES.md after user pick
**Status:** complete
### Phase 5: first commit, private gh repo, push
**Status:** complete

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|

### Phase 6: load + clean steps (core/load.py, core/clean.py, industries/insurance/clean.py)
**Status:** complete

| Error | Attempt | Resolution |
|-------|---------|------------|
| `cat >` with no heredoc hung profile run | 1 | stopped task, rewrote command |
| conda run rejects multi-line `-c` | 1 | call env python.exe directly |
| fill_missing ran after drop_empty_columns, all-null filled column dropped | 1 | fill before drop |
