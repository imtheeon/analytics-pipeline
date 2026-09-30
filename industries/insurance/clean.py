"""Insurance-specific cleaning rules for the auto claims dataset."""

import pandas as pd

from core.clean import clean, save_processed
from core.load import INBOX, load_csv

# Missing collision_type only occurs for Parked Car / Vehicle Theft: no collision happened.
FILLS = {"collision_type": "Not Applicable"}

VALUE_FIXES = {"auto_make": {"Suburu": "Subaru"}}


def clean_claims(df: pd.DataFrame) -> pd.DataFrame:
    """Generic clean plus insurance fills and typo fixes."""
    return clean(df, FILLS).replace(VALUE_FIXES)


if __name__ == "__main__":
    claims = clean_claims(load_csv(INBOX / "insurance_claims.csv"))
    print(f"Saved {len(claims)} rows to {save_processed(claims, 'insurance_claims')}")
