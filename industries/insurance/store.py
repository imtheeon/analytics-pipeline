"""Store the validated claims table and its validation report in DuckDB."""

import pandas as pd

from core.clean import PROCESSED
from core.store import store_tables
from core.validate import raise_on_errors
from industries.insurance.validate import validate_claims

if __name__ == "__main__":
    claims = pd.read_parquet(PROCESSED / "insurance_claims.parquet")
    report = validate_claims(claims)
    raise_on_errors(report)  # never store data that failed an error rule
    path = store_tables({"claims": claims, "validation_report": report})
    print(f"Stored {len(claims)} claims and {len(report)} checks in {path}")
