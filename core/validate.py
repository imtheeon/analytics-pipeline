"""Validate step: rule-based data-quality checks run before storing."""

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

REPORTS = Path("reports")

# A rule is (severity, check). The check takes the table and returns True for every BAD row.
# "error" stops the pipeline; "warn" keeps the rows but lists them in the report.
Check = Callable[[pd.DataFrame], pd.Series]
Rule = tuple[str, Check]


def not_null(*cols: str) -> Check:
    """Bad if any of these columns is missing."""
    return lambda df: df[list(cols)].isna().any(axis=1)


def unique(col: str) -> Check:
    """Bad if the value appears more than once."""
    return lambda df: df[col].duplicated(keep=False)


def between(col: str, low: float, high: float) -> Check:
    """Bad if outside [low, high]. Missing also counts as bad."""
    return lambda df: ~df[col].between(low, high)


def parts_sum_to(total: str, *parts: str) -> Check:
    """Bad if the parts don't add up to the total (float-safe)."""
    return lambda df: ~np.isclose(df[list(parts)].sum(axis=1), df[total])


def not_before(later: str, earlier: str) -> Check:
    """Bad if the 'later' date is before the 'earlier' date."""
    return lambda df: df[later] < df[earlier]


def validate(df: pd.DataFrame, rules: dict[str, Rule]) -> pd.DataFrame:
    """Run every rule; return one report row per rule with the failing row count."""
    rows = []
    for name, (severity, check) in rules.items():
        bad = check(df)
        rows.append(
            {
                "check": name,
                "severity": severity,
                "failed_rows": int(bad.sum()),
                "failed_index": df.index[bad].tolist()[:10],
            }
        )
    return pd.DataFrame(rows)


def raise_on_errors(report: pd.DataFrame) -> None:
    """Stop the pipeline if any 'error' rule failed."""
    errors = report[(report["severity"] == "error") & (report["failed_rows"] > 0)]
    if len(errors):
        raise ValueError(f"Validation failed:\n{errors.to_string(index=False)}")


def save_report(report: pd.DataFrame, name: str, out_dir: Path = REPORTS) -> Path:
    """Save the report as CSV in reports/."""
    path = out_dir / f"validation_{name}.csv"
    report.to_csv(path, index=False)
    return path
