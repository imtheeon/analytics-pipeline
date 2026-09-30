import pandas as pd
import pytest

from core.validate import (
    between,
    not_before,
    not_null,
    parts_sum_to,
    raise_on_errors,
    save_report,
    unique,
    validate,
)
from industries.insurance.validate import validate_claims


def test_not_null():
    df = pd.DataFrame({"a": [1, None], "b": [1, 2]})
    assert not_null("a", "b")(df).tolist() == [False, True]


def test_unique_flags_every_copy():
    df = pd.DataFrame({"id": [1, 1, 2]})
    assert unique("id")(df).tolist() == [True, True, False]


def test_between_flags_out_of_range_and_missing():
    df = pd.DataFrame({"age": [15, 40, None]})
    assert between("age", 16, 100)(df).tolist() == [True, False, True]


def test_parts_sum_to_is_float_safe():
    df = pd.DataFrame({"total": [0.3, 5.0], "a": [0.1, 1.0], "b": [0.2, 1.0]})
    assert parts_sum_to("total", "a", "b")(df).tolist() == [False, True]


def test_not_before():
    df = pd.DataFrame(
        {
            "start": pd.to_datetime(["2015-01-10", "2015-01-10"]),
            "event": pd.to_datetime(["2015-01-09", "2015-01-10"]),
        }
    )
    assert not_before("event", "start")(df).tolist() == [True, False]


def test_validate_report_and_raise():
    df = pd.DataFrame({"id": [1, 1], "x": [5, -1]})
    rules = {
        "id unique": ("error", unique("id")),
        "x positive": ("warn", lambda d: d["x"] < 0),
    }
    report = validate(df, rules)
    assert report["failed_rows"].tolist() == [2, 1]
    assert report.loc[1, "failed_index"] == [1]
    with pytest.raises(ValueError, match="id unique"):
        raise_on_errors(report)


def test_warnings_alone_do_not_raise():
    report = validate(pd.DataFrame({"x": [-1]}), {"x": ("warn", lambda d: d["x"] < 0)})
    raise_on_errors(report)


def test_save_report(tmp_path):
    report = pd.DataFrame({"check": ["a"], "failed_rows": [0]})
    assert save_report(report, "t", tmp_path).read_text().startswith("check,")


def claim(**overrides):
    row = {
        "policy_number": 1,
        "policy_bind_date": pd.Timestamp("2014-01-01"),
        "incident_date": pd.Timestamp("2015-01-01"),
        "incident_type": "Parked Car",
        "total_claim_amount": 300,
        "injury_claim": 100,
        "property_claim": 100,
        "vehicle_claim": 100,
        "age": 30,
        "incident_hour_of_the_day": 5,
        "umbrella_limit": 0,
    }
    return pd.DataFrame([row | overrides])


def test_insurance_rules_pass_on_good_claim():
    assert validate_claims(claim())["failed_rows"].sum() == 0


def test_insurance_rules_catch_bad_claim():
    report = validate_claims(claim(total_claim_amount=999, umbrella_limit=-1))
    failed = set(report.loc[report["failed_rows"] > 0, "check"])
    assert failed == {"claim parts sum to total", "umbrella_limit not negative"}
