import pandas as pd

from core.analyze import run_queries, save_results
from core.store import store_tables
from industries.insurance.analyze import QUERIES


def test_run_queries_and_save(tmp_path):
    db = store_tables({"t": pd.DataFrame({"x": [1, 2, 3]})}, tmp_path / "t.duckdb")
    (tmp_path / "total.sql").write_text("SELECT sum(x) AS total FROM t")
    results = run_queries(tmp_path, db)
    assert results["total"]["total"].tolist() == [6]
    assert save_results(results, tmp_path)[0].name == "analysis_total.csv"


def test_insurance_queries_run_and_add_up(tmp_path):
    claims = pd.DataFrame(
        {
            "incident_date": pd.to_datetime(["2015-01-05", "2015-01-06", "2015-01-20"]),
            "incident_type": ["Parked Car", "Parked Car", "Vehicle Theft"],
            "incident_severity": ["Minor Damage", "Total Loss", "Minor Damage"],
            "incident_state": ["NY", "NY", "SC"],
            "total_claim_amount": [100, 200, 300],
            "fraud_reported": pd.array([True, False, False], dtype="boolean"),
        }
    )
    results = run_queries(
        QUERIES, store_tables({"claims": claims}, tmp_path / "t.duckdb")
    )
    assert results["claims_by_week"]["claims"].tolist() == [2, 1]
    assert results["fraud_by_incident_type"].loc[0, "fraud_pct"] == 50.0
    assert results["claims_by_state"]["pct_of_total_amount"].sum() == 100.0
