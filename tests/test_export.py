import pandas as pd

from core.export import export_csvs


def test_export_writes_iso_dates_without_index(tmp_path):
    df = pd.DataFrame(
        {"id": [1, 2], "incident_date": pd.to_datetime(["2015-01-05", "2015-02-28"])}
    )
    [path] = export_csvs({"claims_clean": df}, tmp_path)
    assert path.name == "claims_clean.csv"
    assert path.read_text().splitlines() == [
        "id,incident_date",
        "1,2015-01-05",
        "2,2015-02-28",
    ]
