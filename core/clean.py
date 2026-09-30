"""Clean step: generic fixes that apply to any table."""

import re
from pathlib import Path

import pandas as pd

PROCESSED = Path("data/processed")

YES_NO = {"YES": True, "Y": True, "NO": False, "N": False}


def to_snake_case(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to snake_case: 'capital-gains' -> 'capital_gains', 'ClaimID' -> 'claim_id'."""

    def snake(name: str) -> str:
        name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
        return re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()

    return df.rename(columns=snake)


def drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop columns with no values at all (e.g. from a trailing comma)."""
    return df.dropna(axis="columns", how="all")


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully identical rows."""
    return df.drop_duplicates(ignore_index=True)


def strip_text(df: pd.DataFrame) -> pd.DataFrame:
    """Trim leading/trailing spaces in text columns; blank-only cells become missing."""
    text = df.select_dtypes("string").columns
    return df.assign(
        **{col: df[col].str.strip().mask(lambda s: s == "") for col in text}
    )


def yes_no_to_bool(df: pd.DataFrame) -> pd.DataFrame:
    """Turn YES/NO or Y/N text columns into booleans; missing stays <NA>."""
    out = df.copy()
    for col in df.select_dtypes("string").columns:
        values = df[col].dropna().str.upper()
        if len(values) and values.isin(list(YES_NO)).all():
            out[col] = df[col].str.upper().map(YES_NO).astype("boolean")
    return out


def fill_missing(df: pd.DataFrame, fills: dict[str, object]) -> pd.DataFrame:
    """Fill missing values per column, e.g. {'collision_type': 'Not Applicable'}."""
    return df.fillna(fills)


def clean(df: pd.DataFrame, fills: dict[str, object] | None = None) -> pd.DataFrame:
    """Run all generic cleaning steps in order."""
    df = to_snake_case(df)
    df = strip_text(df)
    df = fill_missing(df, fills or {})  # before dropping, so a filled column is kept
    df = drop_empty_columns(df)
    df = drop_duplicates(df)
    return yes_no_to_bool(df)


def save_processed(df: pd.DataFrame, name: str, out_dir: Path = PROCESSED) -> Path:
    """Save as Parquet (keeps dates and booleans, unlike CSV)."""
    path = out_dir / f"{name}.parquet"
    df.to_parquet(path, index=False)
    return path
