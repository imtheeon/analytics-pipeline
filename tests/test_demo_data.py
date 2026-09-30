from pathlib import Path

import pandas as pd

from industries.insurance.demo_data import (
    DEMO,
    MIN_GROUP,
    OTHER,
    amount_stats,
    merge_small,
)


def test_merge_small_relabels_small_state_groups():
    df = pd.DataFrame(
        {
            "incident_state": ["NY"] * MIN_GROUP + ["OH"],
            "incident_type": ["Parked Car"] * (MIN_GROUP + 1),
        }
    )
    assert merge_small(df)["incident_type"].tolist() == ["Parked Car"] * MIN_GROUP + [
        OTHER
    ]


def test_amount_stats_are_percentiles_not_min_max():
    df = pd.DataFrame({"incident_type": "Parked Car", "total_claim_amount": range(101)})
    row = amount_stats(df).iloc[0]
    assert [row["p5"], row["median"], row["p95"]] == [5, 50, 95]


def test_demo_data_has_no_claim_rows():
    files = sorted(Path(DEMO).glob("*.csv"))
    assert files
    for path in files:
        df = pd.read_csv(path)
        assert not {"policy_number", "insured_zip", "incident_location"} & set(df)
        assert len(df) < 1000, path.name
    amounts = pd.read_csv(DEMO / "by_state_type.csv")
    assert amounts["claims"].min() >= MIN_GROUP
    assert amounts["claims"].sum() == 1000
