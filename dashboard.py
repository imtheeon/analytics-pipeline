"""Streamlit dashboard for the insurance claims: `streamlit run dashboard.py`.

Reads the claims in DuckDB; without the database it falls back to the aggregated
tables in demo_data/ (demo mode).
"""

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.store import DB_PATH
from industries.insurance.demo_data import DEMO, summarize
from industries.insurance.report import HIGHLIGHT, ranked_bar

NAVY, BLUE, LIGHT_BLUE = "#1f3a5f", "#3d7cc9", "#a9c6e8"
SEVERITIES = ["Trivial Damage", "Minor Damage", "Major Damage", "Total Loss"]
MIN_CLAIMS = 20  # smallest incident type x severity group an insight may single out
DEMO_TABLES = [
    "by_state_type",
    "by_state_type_severity",
    "by_state_type_day",
    "claim_amount_stats",
]
LABELS = {
    "incident_type": "Incident type",
    "incident_severity": "Severity",
    "total_claim_amount": "Claim amount ($)",
    "incident_date": "Date",
}

px.defaults.color_discrete_sequence = [NAVY, BLUE, LIGHT_BLUE]


@st.cache_data
def load_data() -> tuple[dict[str, pd.DataFrame], pd.DataFrame | None]:
    """Summary tables and claim rows from DuckDB, or only the demo_data/ summaries."""
    if DB_PATH.exists():
        with duckdb.connect(DB_PATH, read_only=True) as con:
            rows = con.sql("SELECT * FROM claims").df()
        return summarize(rows), rows
    tables = {name: pd.read_csv(DEMO / f"{name}.csv") for name in DEMO_TABLES}
    day = tables["by_state_type_day"]
    day["incident_date"] = pd.to_datetime(day["incident_date"])
    return tables, None


def select(df: pd.DataFrame, states: list[str], types: list[str]) -> pd.DataFrame:
    """Rows matching the filters; a table without a state column ignores that filter."""
    if states and "incident_state" in df:
        df = df[df["incident_state"].isin(states)]
    if types:
        df = df[df["incident_type"].isin(types)]
    return df


def fraud_rate_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Percent of claims reported as fraud, per value of col, from a summary table."""
    out = df.groupby(col, as_index=False)[["claims", "fraud_claims"]].sum()
    out["fraud_pct"] = (100 * out.pop("fraud_claims") / out.pop("claims")).round(1)
    return out


def daily_claims(day: pd.DataFrame) -> pd.DataFrame:
    """Claims per day (days without claims count as 0) and their 14-day rolling mean."""
    daily = day.groupby("incident_date")["claims"].sum().resample("D").sum()
    daily = daily.to_frame()
    daily["avg_14d"] = daily["claims"].rolling(14).mean()
    return daily.reset_index()


def insights(t: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    """Plain-language findings, every number computed from the filtered summary tables."""
    by_type, sev = t["by_state_type"], t["by_state_type_severity"]
    n, n_fraud = by_type["claims"].sum(), by_type["fraud_claims"].sum()
    daily = daily_claims(t["by_state_type_day"])
    start, end = daily["incident_date"].min(), daily["incident_date"].max()
    days = len(daily)

    by_sev = sev.groupby("incident_severity").agg(
        sum=("fraud_claims", "sum"), size=("claims", "sum")
    )
    by_sev["mean"] = by_sev["sum"] / by_sev["size"]
    by_sev = by_sev.sort_values("mean")
    cost = by_type.groupby("incident_type").agg(
        sum=("total_claim_amount", "sum"), size=("claims", "sum")
    )
    cost["mean"] = cost["sum"] / cost["size"]
    top = cost["mean"].idxmax()
    key = [
        (
            f"{by_sev.index[-1]} claims have the highest fraud rate at "
            f"{by_sev['mean'].iloc[-1]:.1%} ({by_sev['sum'].iloc[-1]:.0f} of "
            f"{by_sev['size'].iloc[-1]:.0f}), versus {n_fraud / n:.1%} across all "
            f"{n:,} selected claims."
        ),
        (
            f"{top} claims cost the most on average (${cost.loc[top, 'mean']:,.0f}) "
            f"and make up {cost.loc[top, 'sum'] / cost['sum'].sum():.0%} "
            "of total claim cost."
        ),
    ]

    daily = daily["claims"]
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

    combos = sev.groupby(["incident_type", "incident_severity"]).agg(
        sum=("fraud_claims", "sum"), size=("claims", "sum")
    )
    combos["mean"] = combos["sum"] / combos["size"]
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
            f'"Fraud" is the dataset\'s `fraud_reported` label ({n_fraud:,} '
            f"of {n:,} claims), not proof of fraud; every pattern here is a "
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
    tables, rows = load_data()
    if rows is None:
        st.info("Demo mode: aggregated data only.")
    totals = tables["by_state_type"]

    # An empty selection means "all".
    st.sidebar.header("Filters")
    states = st.sidebar.multiselect("State", sorted(totals["incident_state"].unique()))
    types = st.sidebar.multiselect(
        "Incident type", sorted(totals["incident_type"].unique())
    )
    t = {name: select(table, states, types) for name, table in tables.items()}
    df = t["by_state_type"]
    if df.empty:
        st.warning("No claims match these filters.")
        st.stop()

    daily = daily_claims(t["by_state_type_day"])
    start, end = daily["incident_date"].min(), daily["incident_date"].max()
    n, all_n = df["claims"].sum(), totals["claims"].sum()
    st.caption(
        f"Incidents from {start:%b} {start.day}, {start.year} to {end:%b} {end.day}, {end.year} · "
        f"{n:,} of {all_n:,} claims"
    )

    cost, all_cost = df["total_claim_amount"].sum(), totals["total_claim_amount"].sum()
    rate, avg = df["fraud_claims"].sum() / n, cost / n
    if states or types:
        helpers = [
            f"{n / all_n:.1%} of all claims",
            f"{cost / all_cost:.1%} of total cost",
            (
                f"{100 * (rate - totals['fraud_claims'].sum() / all_n):+.1f} pts "
                "vs. dataset average"
            ),
            f"{avg / (all_cost / all_n) - 1:+.0%} vs. dataset average",
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
        n_fraud = int(df["fraud_claims"].sum())
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
        title = "Claim amount distribution by incident type"
        if rows is None:
            stats = t["claim_amount_stats"]
            box = go.Figure(
                go.Box(
                    x=stats["incident_type"],
                    q1=stats["q1"],
                    median=stats["median"],
                    q3=stats["q3"],
                    lowerfence=stats["p5"],
                    upperfence=stats["p95"],
                )
            ).update_layout(
                title=title,
                xaxis_title="Incident type",
                yaxis_title="Claim amount ($)",
            )
            c2.plotly_chart(box)
            c2.caption(
                "Whiskers show the 5th to 95th percentile. In demo mode this chart "
                "ignores the State filter."
            )
        else:
            c2.plotly_chart(
                px.box(
                    select(rows, states, types),
                    x="incident_type",
                    y="total_claim_amount",
                    labels=LABELS,
                    title=title,
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
                fraud_rate_by(t["by_state_type_severity"], "incident_severity"),
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
        heat = t["by_state_type_severity"].pivot_table(
            index="incident_type",
            columns="incident_severity",
            values=["fraud_claims", "claims"],
            aggfunc="sum",
        )
        heat = heat["fraud_claims"] / heat["claims"]
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
                claims=("claims", "sum"),
                total_cost=("total_claim_amount", "sum"),
                fraud_claims=("fraud_claims", "sum"),
            )
            .reset_index()
            .sort_values("total_cost", ascending=False)
        )
        by_state["avg_claim"] = by_state["total_cost"] / by_state["claims"]
        by_state["avg_claim"] = by_state["avg_claim"].round().astype(int)
        by_state["fraud_pct"] = 100 * by_state.pop("fraud_claims") / by_state["claims"]
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
        daily = daily.rename(
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
        for section, lines in insights(t).items():
            st.subheader(section)
            # Escape $ so Streamlit doesn't render dollar amounts as LaTeX.
            st.markdown("\n".join(f"- {line.replace('$', r'\$')}" for line in lines))


if __name__ == "__main__":
    main()
