"""Analyze step: run every .sql file in a folder against the DuckDB file."""

from pathlib import Path

import duckdb
import pandas as pd

from core.store import DB_PATH
from core.validate import REPORTS


def run_queries(sql_dir: Path, db_path: Path = DB_PATH) -> dict[str, pd.DataFrame]:
    """Run each .sql file (read-only); results keyed by file name without extension."""
    with duckdb.connect(db_path, read_only=True) as con:
        return {
            p.stem: con.sql(p.read_text()).df() for p in sorted(sql_dir.glob("*.sql"))
        }


def save_results(
    results: dict[str, pd.DataFrame], out_dir: Path = REPORTS
) -> list[Path]:
    """Save each result as reports/analysis_<name>.csv."""
    paths = []
    for name, df in results.items():
        path = out_dir / f"analysis_{name}.csv"
        df.to_csv(path, index=False)
        paths.append(path)
    return paths
