import pandas as pd

from core.clean import (
    clean,
    drop_duplicates,
    drop_empty_columns,
    fill_missing,
    save_processed,
    strip_text,
    to_snake_case,
    yes_no_to_bool,
)
from industries.insurance.clean import clean_claims


def test_to_snake_case():
    df = pd.DataFrame(columns=["capital-gains", "ClaimID", "Policy State "])
    assert to_snake_case(df).columns.tolist() == [
        "capital_gains",
        "claim_id",
        "policy_state",
    ]


def test_drop_empty_columns():
    df = pd.DataFrame({"a": [1, 2], "_c39": [None, None]})
    assert drop_empty_columns(df).columns.tolist() == ["a"]


def test_drop_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2]})
    assert drop_duplicates(df)["a"].tolist() == [1, 2]


def test_strip_text():
    df = pd.DataFrame({"city": [" Columbus ", "Arlington"]})
    assert strip_text(df)["city"].tolist() == ["Columbus", "Arlington"]


def test_yes_no_to_bool_keeps_missing_and_skips_other_text():
    df = pd.DataFrame(
        {
            "damage": ["YES", "NO", None],
            "fraud": ["Y", "N", "Y"],
            "city": ["A", "B", "C"],
        }
    )
    out = yes_no_to_bool(df)
    assert out["damage"].tolist() == [True, False, pd.NA]
    assert out["fraud"].dtype == "boolean"
    assert out["city"].tolist() == ["A", "B", "C"]


def test_fill_missing():
    df = pd.DataFrame({"collision_type": ["Rear Collision", None]})
    assert fill_missing(df, {"collision_type": "Not Applicable"})[
        "collision_type"
    ].tolist() == [
        "Rear Collision",
        "Not Applicable",
    ]


def test_clean_runs_all_steps():
    df = pd.DataFrame(
        {"Fraud-Reported": ["Y", "Y", "N"], "_c39": [None] * 3, "id": [1, 1, 2]}
    )
    out = clean(df)
    assert out.columns.tolist() == ["fraud_reported", "id"]
    assert len(out) == 2


def test_clean_claims_insurance_rules():
    df = pd.DataFrame({"collision_type": [None], "auto_make": ["Suburu"]})
    out = clean_claims(df)
    assert out.loc[0, "collision_type"] == "Not Applicable"
    assert out.loc[0, "auto_make"] == "Subaru"


def test_save_processed_keeps_dtypes(tmp_path):
    df = pd.DataFrame(
        {"d": pd.to_datetime(["2015-01-01"]), "b": pd.array([True], dtype="boolean")}
    )
    back = pd.read_parquet(save_processed(df, "t", tmp_path))
    assert back.dtypes.equals(df.dtypes)
