"""Write aggregated tables to demo_data/ for the public dashboard demo.

The raw claims can't be published, so these tables hold only counts, totals and
summary statistics: no claim rows, no policy numbers.
"""

from pathlib import Path

import duckdb
import pandas as pd

from core.analyze import run_queries
from core.export import export_csvs
from core.store import DB_PATH
from industries.insurance.analyze import QUERIES

DEMO = Path("demo_data")
KEYS = ["incident_state", "incident_type"]
MIN_GROUP = 10  # state x incident type groups smaller than this are merged
OTHER = "Other (small groups)"
AMOUNTS = ["total_claim_amount", "injury_claim", "property_claim", "vehicle_claim"]


def summarize(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """The tables the dashboard draws from; each can be filtered by state and type."""
    counts = {
        "claims": ("fraud_reported", "size"),
        "fraud_claims": ("fraud_reported", "sum"),
    }
    return {
        "by_state_type": df.groupby(KEYS, as_index=False).agg(
            **counts, **{col: (col, "sum") for col in AMOUNTS}
        ),
        "by_state_type_severity": df.groupby(
            [*KEYS, "incident_severity"], as_index=False
        ).agg(**counts),
        "by_state_type_day": df.groupby([*KEYS, "incident_date"], as_index=False)
        .size()
        .rename(columns={"size": "claims"}),
    }


def merge_small(df: pd.DataFrame) -> pd.DataFrame:
    """Relabel the incident type of small state groups so no total covers only a few claims."""
    size = df.groupby(KEYS)["incident_type"].transform("size")
    return df.assign(incident_type=df["incident_type"].where(size >= MIN_GROUP, OTHER))


def amount_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Box-plot inputs per incident type; whiskers at the 5th/95th percentile, not min/max."""
    stats = df.groupby("incident_type")["total_claim_amount"]
    stats = stats.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).unstack()
    stats.columns = ["p5", "q1", "median", "q3", "p95"]
    return stats.round().reset_index()


if __name__ == "__main__":
    with duckdb.connect(DB_PATH, read_only=True) as con:
        claims = con.sql("SELECT * FROM claims").df()
    tables = summarize(merge_small(claims)) | {
        "claim_amount_stats": amount_stats(claims)
    }
    paths = export_csvs(tables | run_queries(QUERIES), DEMO)
    print(f"Wrote {len(paths)} summary CSVs to {DEMO}/")
