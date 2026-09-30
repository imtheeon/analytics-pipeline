"""Insurance-specific validation rules for the cleaned auto claims table."""

import pandas as pd

from core.clean import PROCESSED
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

AMOUNTS = ["total_claim_amount", "injury_claim", "property_claim", "vehicle_claim"]

RULES = {
    "key columns present": (
        "error",
        not_null(
            "policy_number", "incident_date", "total_claim_amount", "incident_type"
        ),
    ),
    "policy_number unique": ("error", unique("policy_number")),
    "claim parts sum to total": (
        "error",
        parts_sum_to("total_claim_amount", *AMOUNTS[1:]),
    ),
    "claim amounts not negative": (
        "error",
        lambda df: (df[AMOUNTS] < 0).any(axis=1),
    ),
    "age 16-100": ("error", between("age", 16, 100)),
    "incident hour 0-23": ("error", between("incident_hour_of_the_day", 0, 23)),
    # Source errors seen in profiling: keep the rows, flag them for review.
    "umbrella_limit not negative": ("warn", lambda df: df["umbrella_limit"] < 0),
    "incident on/after policy start": (
        "warn",
        not_before("incident_date", "policy_bind_date"),
    ),
}


def validate_claims(df: pd.DataFrame) -> pd.DataFrame:
    """Run the insurance rules and return the report."""
    return validate(df, RULES)


if __name__ == "__main__":
    report = validate_claims(pd.read_parquet(PROCESSED / "insurance_claims.parquet"))
    print(report.to_string(index=False))
    print(f"Report saved to {save_report(report, 'insurance_claims')}")
    raise_on_errors(report)
