"""Streamlit dashboard for the insurance claims in DuckDB: `streamlit run dashboard.py`."""

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from core.store import DB_PATH
from industries.insurance.report import HIGHLIGHT, ranked_bar

NAVY, BLUE, LIGHT_BLUE = "#1f3a5f", "#3d7cc9", "#a9c6e8"
SEVERITIES = ["Trivial Damage", "Minor Damage", "Major Damage", "Total Loss"]
MIN_CLAIMS = 20  # smallest incident type x severity group an insight may single out
LABELS = {
    "incident_type": "Incident type",
    "incident_severity": "Severity",
    "total_claim_amount": "Claim amount ($)",
    "incident_date": "Date",
}

px.defaults.color_discrete_sequence = [NAVY, BLUE, LIGHT_BLUE]


@st.cache_data
def load_claims() -> pd.DataFrame:
    with duckdb.connect(DB_PATH, read_only=True) as con:
        return con.sql("SELECT * FROM claims").df()


def fraud_rate_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Percent of claims reported as fraud, per value of col."""
    out = df.groupby(col, as_index=False)["fraud_reported"].mean()
    out["fraud_pct"] = (100 * out.pop("fraud_reported")).round(1)
    return out


def daily_claims(df: pd.DataFrame) -> pd.DataFrame:
    """Claims per day (days without claims count as 0) and their 14-day rolling mean."""
    daily = df.set_index("incident_date").resample("D").size().rename("claims")
    daily = daily.to_frame()
    daily["avg_14d"] = daily["claims"].rolling(14).mean()
    return daily.reset_index()


def insights(df: pd.DataFrame) -> dict[str, list[str]]:
    """Plain-language findings, every number computed from df (the filtered claims)."""
    fraud = df["fraud_reported"]
    start, end = df["incident_date"].min(), df["incident_date"].max()
    days = (end - start).days + 1

    by_sev = df.groupby("incident_severity")["fraud_reported"]
    by_sev = by_sev.agg(["mean", "sum", "size"]).sort_values("mean")
    cost = df.groupby("incident_type")["total_claim_amount"].agg(["mean", "sum"])
    top = cost["mean"].idxmax()
    key = [
        (
            f"{by_sev.index[-1]} claims have the highest fraud rate at "
            f"{by_sev['mean'].iloc[-1]:.1%} ({by_sev['sum'].iloc[-1]:.0f} of "
            f"{by_sev['size'].iloc[-1]:.0f}), versus {fraud.mean():.1%} across all "
            f"{len(df):,} selected claims."
        ),
        (
            f"{top} claims cost the most on average (${cost.loc[top, 'mean']:,.0f}) "
            f"and make up {cost.loc[top, 'sum'] / cost['sum'].sum():.0%} "
            "of total claim cost."
        ),
    ]

    daily = daily_claims(df)["claims"]
    if len(daily) < 14:
        trends = [f"Only {len(daily)} days are selected, too few to compare periods."]
    else:
        half = len(daily) // 2
        first, second = daily[:half].mean(), daily[half:].mean()
        trends = [
            (
                f"Claims averaged {first:.1f} per day in the first half of the period "
                f"and {second:.1f} in the second half ({second - first:+.1f} per day)."
            )
        ]

    combos = df.groupby(["incident_type", "incident_severity"])["fraud_reported"]
    combos = combos.agg(["mean", "size"])
    combos = combos[combos["size"] >= MIN_CLAIMS]
    if combos.empty:
        watch = [
            (
                f"No incident type and severity combination has {MIN_CLAIMS}+ claims "
                "under these filters, so none is singled out."
            )
        ]
    else:
        itype, isev = combos["mean"].idxmax()
        row = combos.loc[(itype, isev)]
        watch = [
            (
                f"{itype} claims with {isev}: {row['mean']:.0%} of {row['size']:.0f} "
                "are flagged as fraud, the highest of any combination with "
                f"{MIN_CLAIMS}+ claims. These deserve a closer look in the next review."
            )
        ]

    caveats = [
        (
            f"The data covers only {days} days ({start:%b} {start.day} to {end:%b} {end.day}, {end.year}, "
            f"about {days / 30:.1f} months), too short for a reliable forecast "
            "or any seasonal pattern."
        ),
        (
            f'"Fraud" is the dataset\'s `fraud_reported` label ({int(fraud.sum()):,} '
            f"of {len(df):,} claims), not proof of fraud; every pattern here is a "
            "correlation."
        ),
    ]
    return {
        "Key findings": key,
        "Trends": trends,
        "What to watch next": watch,
        "Caveats": caveats,
    }


def main() -> None:
    st.set_page_config(page_title="Insurance Claims", layout="wide")
    st.title("Insurance Claims Dashboard")
    st.markdown("Claim volume, cost and reported fraud for auto insurance claims.")
    claims = load_claims()

    # An empty selection means "all".
    st.sidebar.header("Filters")
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

    start, end = df["incident_date"].min(), df["incident_date"].max()
    st.caption(
        f"Incidents from {start:%b} {start.day}, {start.year} to {end:%b} {end.day}, {end.year} · "
        f"{len(df):,} of {len(claims):,} claims"
    )

    n, cost = len(df), df["total_claim_amount"].sum()
    rate, avg = df["fraud_reported"].mean(), df["total_claim_amount"].mean()
    if states or types:
        helpers = [
            f"{n / len(claims):.1%} of all claims",
            f"{cost / claims['total_claim_amount'].sum():.1%} of total cost",
            (
                f"{100 * (rate - claims['fraud_reported'].mean()):+.1f} pts "
                "vs. dataset average"
            ),
            f"{avg / claims['total_claim_amount'].mean() - 1:+.0%} vs. dataset average",
        ]
    else:
        helpers = ["All claims", "All claims", "Dataset average", "Dataset average"]
    values = {
        "Total claims": f"{n:,}",
        "Total claim amount": (
            f"${cost / 1e6:,.1f}M" if cost >= 1e6 else f"${cost:,.0f}"
        ),
        "Fraud rate": f"{rate:.1%}",
        "Average claim": f"${avg:,.0f}",
    }
    for col, (label, value), helper in zip(st.columns(4), values.items(), helpers):
        with col.container(border=True):
            st.metric(label, value)
            st.caption(helper)

    overview, fraud, geography, trends, notes = st.tabs(
        ["Overview", "Fraud", "Geography", "Trends", "Insights"]
    )

    with overview:
        c1, c2 = st.columns([1, 2])
        n_fraud = int(df["fraud_reported"].sum())
        names = ["Flagged as fraud", "Not flagged"]
        c1.plotly_chart(
            px.pie(
                names=names,
                values=[n_fraud, n - n_fraud],
                color=names,
                color_discrete_map=dict(zip(names, [HIGHLIGHT, NAVY])),
                hole=0.6,
                title="Share of claims flagged as fraud",
            )
        )
        c2.plotly_chart(
            px.box(
                df,
                x="incident_type",
                y="total_claim_amount",
                labels=LABELS,
                title="Claim amount distribution by incident type",
            )
        )
        parts = df.groupby("incident_type")[
            ["injury_claim", "property_claim", "vehicle_claim"]
        ].sum()
        parts.columns = ["Injury", "Property", "Vehicle"]
        parts = parts.loc[parts.sum(axis=1).sort_values(ascending=False).index]
        st.plotly_chart(
            px.bar(
                parts,
                labels={"value": "Claim cost ($)", "variable": "Part", **LABELS},
                title="Claim cost split by incident type",
            )
        )

    with fraud:
        c1, c2 = st.columns(2)
        c1.plotly_chart(
            ranked_bar(
                fraud_rate_by(df, "incident_severity"),
                "incident_severity",
                "fraud_pct",
                "Fraud rate by severity (%)",
            ).update_layout(xaxis_title="Fraud rate (%)")
        )
        c2.plotly_chart(
            ranked_bar(
                fraud_rate_by(df, "incident_type"),
                "incident_type",
                "fraud_pct",
                "Fraud rate by incident type (%)",
            ).update_layout(xaxis_title="Fraud rate (%)")
        )
        heat = df.pivot_table(
            index="incident_type",
            columns="incident_severity",
            values="fraud_reported",
            aggfunc="mean",
        )
        heat = heat[[s for s in SEVERITIES if s in heat.columns]]
        st.plotly_chart(
            px.imshow(
                (100 * heat).round(0),
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Blues",
                labels={"x": "Severity", "y": "Incident type", "color": "Fraud %"},
                title="Fraud rate by incident type and severity (%)",
            )
        )
        st.caption("Blank cells: no claims with that combination.")

    with geography:
        by_state = (
            df.groupby("incident_state")
            .agg(
                claims=("total_claim_amount", "size"),
                total_cost=("total_claim_amount", "sum"),
                avg_claim=("total_claim_amount", "mean"),
                fraud_pct=("fraud_reported", "mean"),
            )
            .reset_index()
            .sort_values("total_cost", ascending=False)
        )
        by_state["fraud_pct"] = 100 * by_state["fraud_pct"]
        by_state["avg_claim"] = by_state["avg_claim"].round().astype(int)
        c1, c2 = st.columns([3, 2])
        c1.plotly_chart(
            ranked_bar(
                by_state, "incident_state", "total_cost", "Claim cost by state ($)"
            )
            .update_traces(texttemplate="$%{x:,.0f}")
            .update_layout(xaxis_title="Claim cost ($)")
        )
        c2.dataframe(
            by_state,
            hide_index=True,
            column_config={
                "incident_state": "State",
                "claims": "Claims",
                "total_cost": st.column_config.NumberColumn(
                    "Total cost", format="dollar"
                ),
                "avg_claim": st.column_config.NumberColumn(
                    "Avg claim", format="dollar"
                ),
                "fraud_pct": st.column_config.NumberColumn(
                    "Fraud rate", format="%.1f%%"
                ),
            },
        )

    with trends:
        daily = daily_claims(df).rename(
            columns={"claims": "Daily claims", "avg_14d": "2-week average"}
        )
        fig = px.line(
            daily,
            x="incident_date",
            y=["Daily claims", "2-week average"],
            color_discrete_sequence=[LIGHT_BLUE, NAVY],
            labels={"value": "Claims", "variable": "", **LABELS},
            title="Claims per day with 2-week rolling average",
        )
        st.plotly_chart(
            fig.update_traces(line_width=3, selector={"name": "2-week average"})
        )
        st.caption("The 2-week average starts on day 14, once it has 14 days of data.")

    with notes:
        for section, lines in insights(df).items():
            st.subheader(section)
            # Escape $ so Streamlit doesn't render dollar amounts as LaTeX.
            st.markdown("\n".join(f"- {line.replace('$', r'\$')}" for line in lines))


if __name__ == "__main__":
    main()
