"""Export the cleaned claims table and every summary query as CSVs for Power BI."""

import duckdb

from core.analyze import run_queries
from core.export import POWERBI, export_csvs
from core.store import DB_PATH
from industries.insurance.analyze import QUERIES

if __name__ == "__main__":
    with duckdb.connect(DB_PATH, read_only=True) as con:
        claims = con.sql("SELECT * FROM claims").df()
    paths = export_csvs({"claims_clean": claims} | run_queries(QUERIES))
    print(f"Exported {len(paths)} CSVs to {POWERBI}/")
