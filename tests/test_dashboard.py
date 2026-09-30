from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import dashboard
from industries.insurance.demo_data import summarize


def claims(days: int) -> pd.DataFrame:
    """Two claims per day: a fraudulent Total Loss theft and a clean Minor collision."""
    dates = pd.date_range("2015-01-01", periods=days).repeat(2)
    return pd.DataFrame(
        {
            "incident_date": dates,
            "incident_state": "NY",
            "incident_type": ["Vehicle Theft", "Parked Car"] * days,
            "incident_severity": ["Total Loss", "Minor Damage"] * days,
            "total_claim_amount": [9000, 1000] * days,
            "injury_claim": 0,
            "property_claim": 0,
            "vehicle_claim": [9000, 1000] * days,
            "fraud_reported": [True, False] * days,
        }
    )


def test_dashboard_imports_and_computes_fraud_rate():
    out = dashboard.fraud_rate_by(
        summarize(claims(2))["by_state_type"], "incident_type"
    )
    assert callable(dashboard.main)
    assert out["fraud_pct"].tolist() == [0.0, 100.0]


def test_insights_are_computed_from_the_data():
    notes = dashboard.insights(summarize(claims(60)))
    assert list(notes) == ["Key findings", "Trends", "What to watch next", "Caveats"]
    assert 5 <= sum(len(lines) for lines in notes.values()) <= 6
    assert notes["Key findings"][0].startswith(
        "Total Loss claims have the highest fraud rate at 100.0% (60 of 60)"
    )
    assert "90%" in notes["Key findings"][1]  # theft share of total cost
    assert "(+0.0 per day)" in notes["Trends"][0]
    assert (
        "Vehicle Theft claims with Total Loss: 100% of 60"
        in notes["What to watch next"][0]
    )
    caveats = " ".join(notes["Caveats"])
    assert "60 days" in caveats and "forecast" in caveats
    assert "label" in caveats and "not proof" in caveats


def test_insights_handle_short_and_small_selections():
    notes = dashboard.insights(summarize(claims(5)))
    assert "too few to compare" in notes["Trends"][0]
    assert "none is singled out" in notes["What to watch next"][0]


def test_demo_mode_runs_without_the_database(monkeypatch, tmp_path):
    monkeypatch.setattr("core.store.DB_PATH", tmp_path / "missing.duckdb")
    app = Path(dashboard.__file__).resolve().as_posix()
    at = AppTest.from_file(app, default_timeout=30).run()
    assert not at.exception
    assert at.info[0].value == "Demo mode: aggregated data only."
    assert at.metric[0].value == "1,000"

    at.sidebar.multiselect[0].select("NY").run()
    assert not at.exception
    assert at.metric[0].value != "1,000"
