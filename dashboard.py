"""Streamlit dashboard for the insurance claims in DuckDB: `streamlit run dashboard.py`."""

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from core.store import DB_PATH
from industries.insurance.report import ranked_bar


@st.cache_data
def load_claims() -> pd.DataFrame:
    with duckdb.connect(DB_PATH, read_only=True) as con:
        return con.sql("SELECT * FROM claims").df()


def fraud_rate_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Percent of claims reported as fraud, per value of col."""
    out = df.groupby(col, as_index=False)["fraud_reported"].mean()
    out["fraud_pct"] = (100 * out.pop("fraud_reported")).round(1)
    return out


def main() -> None:
    st.set_page_config(page_title="Insurance Claims", layout="wide")
    st.title("Insurance Claims")
    claims = load_claims()

    # An empty selection means "all".
    states = st.sidebar.multiselect("State", sorted(claims["incident_state"].unique()))
    types = st.sidebar.multiselect(
        "Incident type", sorted(claims["incident_type"].unique())
    )
    df = claims
    if states:
        df = df[df["incident_state"].isin(states)]
    if types:
        df = df[df["incident_type"].isin(types)]
    if df.empty:
        st.warning("No claims match these filters.")
        st.stop()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total claims", f"{len(df):,}")
    k2.metric("Total claim amount", f"${df['total_claim_amount'].sum():,.0f}")
    k3.metric("Fraud rate", f"{df['fraud_reported'].mean():.1%}")
    k4.metric("Average claim", f"${df['total_claim_amount'].mean():,.0f}")

    c1, c2 = st.columns(2)
    c1.plotly_chart(
        ranked_bar(
            fraud_rate_by(df, "incident_severity"),
            "incident_severity",
            "fraud_pct",
            "Fraud rate by severity (%)",
        )
    )
    c2.plotly_chart(
        ranked_bar(
            fraud_rate_by(df, "incident_type"),
            "incident_type",
            "fraud_pct",
            "Fraud rate by incident type (%)",
        )
    )

    c3, c4 = st.columns(2)
    by_state = df.groupby("incident_state", as_index=False)["total_claim_amount"].sum()
    c3.plotly_chart(
        ranked_bar(
            by_state, "incident_state", "total_claim_amount", "Claim cost by state ($)"
        )
    )
    weekly = (
        df.groupby(df["incident_date"].dt.to_period("W").dt.start_time)
        .size()
        .rename_axis("week_start")
        .reset_index(name="claims")
    )
    c4.plotly_chart(
        px.line(
            weekly, x="week_start", y="claims", title="Claims per week", markers=True
        )
    )


if __name__ == "__main__":
    main()
