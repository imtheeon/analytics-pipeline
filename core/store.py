"""Store step: write DataFrames into a DuckDB file as tables."""

from pathlib import Path

import duckdb
import pandas as pd

from core.clean import PROCESSED

DB_PATH = PROCESSED / "claims.duckdb"


def store_tables(tables: dict[str, pd.DataFrame], db_path: Path = DB_PATH) -> Path:
    """Write each DataFrame as a table; re-running replaces the table, never appends."""
    with duckdb.connect(db_path) as con:
        for name, df in tables.items():
            con.register("incoming", df)
            con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM incoming')
            con.unregister("incoming")
    return db_path
