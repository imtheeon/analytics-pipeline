"""Export step: write DataFrames as Power BI-ready CSVs."""

from pathlib import Path

import pandas as pd

from core.validate import REPORTS

POWERBI = REPORTS / "powerbi"


def export_csvs(tables: dict[str, pd.DataFrame], out_dir: Path = POWERBI) -> list[Path]:
    """Write each DataFrame as <name>.csv: no index column, dates as YYYY-MM-DD."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, df in tables.items():
        path = out_dir / f"{name}.csv"
        df.to_csv(path, index=False, date_format="%Y-%m-%d")
        paths.append(path)
    return paths
