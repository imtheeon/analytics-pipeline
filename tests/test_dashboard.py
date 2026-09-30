import pandas as pd

import dashboard


def test_dashboard_imports_and_computes_fraud_rate():
    df = pd.DataFrame(
        {"incident_type": ["A", "A", "B"], "fraud_reported": [True, False, False]}
    )
    out = dashboard.fraud_rate_by(df, "incident_type")
    assert callable(dashboard.main)
    assert out["fraud_pct"].tolist() == [50.0, 0.0]
