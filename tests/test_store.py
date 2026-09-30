import duckdb
import pandas as pd

from core.store import store_tables
from core.validate import unique, validate


def test_store_twice_replaces_not_duplicates(tmp_path):
    db = tmp_path / "t.duckdb"
    df = pd.DataFrame({"id": [1, 2], "d": pd.to_datetime(["2015-01-01", "2015-01-02"])})
    store_tables({"claims": df}, db)
    store_tables({"claims": df}, db)
    with duckdb.connect(db) as con:
        assert con.sql("SELECT count(*) FROM claims").fetchone()[0] == 2
        assert (
            con.sql("SELECT typeof(d) FROM claims LIMIT 1").fetchone()[0] == "TIMESTAMP"
        )


def test_store_validation_report(tmp_path):
    db = tmp_path / "t.duckdb"
    report = validate(
        pd.DataFrame({"id": [1, 1, 2]}), {"id unique": ("error", unique("id"))}
    )
    store_tables({"validation_report": report}, db)
    with duckdb.connect(db) as con:
        row = con.sql(
            'SELECT "check", failed_rows, failed_index FROM validation_report'
        ).fetchone()
    assert row == ("id unique", 2, [0, 1])
