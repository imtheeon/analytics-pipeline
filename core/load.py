"""Load step: read raw CSVs from data/inbox with correct dtypes."""

from pathlib import Path

import pandas as pd

INBOX = Path("data/inbox")

# Only "?" and empty cells mean missing. pandas' default list would also turn
# real values like "None" or "NA" into missing.
NA_VALUES = ["?", ""]


def load_csv(path: Path) -> pd.DataFrame:
    """Read one CSV and turn every column with 'date' in its name into datetimes."""
    df = pd.read_csv(path, na_values=NA_VALUES, keep_default_na=False)
    # ponytail: dates found by column name; switch to value sniffing if a source names them differently
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], format="ISO8601")
    return df


def load_inbox(inbox: Path = INBOX) -> dict[str, pd.DataFrame]:
    """Load every CSV in the inbox, keyed by file name without extension."""
    return {path.stem: load_csv(path) for path in sorted(inbox.glob("*.csv"))}
