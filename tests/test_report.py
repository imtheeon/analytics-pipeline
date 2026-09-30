import pandas as pd
import plotly.express as px

from core.report import build_html, save_html
from industries.insurance.report import build_sections


def test_build_html_loads_plotly_once(tmp_path):
    fig = px.bar(x=["a"], y=[1])
    table = pd.DataFrame({"x": [1]})
    html = build_html("T", [("One", "text", fig, table), ("Two", "more", fig, None)])
    assert html.count("cdn.plot.ly") == 1
    assert "<h2>Two</h2>" in html and "<table" in html
    assert save_html(html, "t", tmp_path).read_text(encoding="utf-8") == html


def test_insurance_headlines_come_from_data():
    results = {
        "fraud_by_severity": pd.DataFrame(
            {
                "incident_severity": ["Major Damage", "Minor Damage"],
                "claims": [10, 10],
                "fraud_claims": [6, 1],
                "fraud_pct": [60.0, 10.0],
            }
        ),
        "fraud_by_incident_type": pd.DataFrame(
            {
                "incident_type": ["Parked Car", "Theft"],
                "fraud_pct": [35.0, 5.0],
                "avg_amount": [100.0, 900.0],
            }
        ),
        "claims_by_state": pd.DataFrame(
            {
                "incident_state": ["NY", "SC", "WV", "OH"],
                "total_amount": [40, 30, 20, 10],
                "pct_of_total_amount": [40.0, 30.0, 20.0, 10.0],
            }
        ),
        "claims_by_week": pd.DataFrame(
            {
                "week_start": pd.to_datetime(["2015-01-05"]),
                "first_day": pd.to_datetime(["2015-01-05"]),
                "last_day": pd.to_datetime(["2015-01-09"]),
                "claims": [20],
            }
        ),
    }
    validation = pd.DataFrame(
        {"check": ["a", "b"], "severity": ["error", "warn"], "failed_rows": [0, 1]}
    )
    sections = {s[0]: s for s in build_sections(results, validation)}
    assert "2015-01-05 to 2015-01-09. 7 claims (35.0%)" in sections["Summary"][1]
    assert "Major Damage" in sections["Fraud by severity"][2].layout.title.text
    assert (
        "NY, SC, WV account for 90%"
        in sections["Claim cost by state"][2].layout.title.text
    )
    assert "1 warning" in sections["Data quality"][1]
    assert (
        "Highest fraud rate: Parked Car (35.0%). Highest average claim: Theft ($900)."
        == sections["Fraud by incident type"][1]
    )
