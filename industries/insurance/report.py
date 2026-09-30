"""Build the insurance claims report from the analysis queries and validation results."""

import duckdb
import pandas as pd
import plotly.express as px

from core.analyze import run_queries
from core.report import Section, build_html, save_html
from core.store import DB_PATH
from core.validate import raise_on_errors
from industries.insurance.analyze import QUERIES

HIGHLIGHT, MUTED = "#d62728", "#9aa5b1"


def ranked_bar(df: pd.DataFrame, label: str, value: str, title: str):
    """Horizontal bar chart, largest on top and highlighted, the rest grey."""
    df = df.sort_values(value)
    colors = [MUTED] * (len(df) - 1) + [HIGHLIGHT]
    fig = px.bar(df, x=value, y=label, orientation="h", title=title, text=value)
    fig.update_traces(marker_color=colors)
    return fig.update_layout(xaxis_rangemode="tozero", yaxis_title=None)


def build_sections(
    results: dict[str, pd.DataFrame], validation: pd.DataFrame
) -> list[Section]:
    """Write the report sections; headline numbers are computed, not hard-coded."""
    sev, kind = results["fraud_by_severity"], results["fraud_by_incident_type"]
    state, week = results["claims_by_state"], results["claims_by_week"]
    claims, fraud = sev["claims"].sum(), sev["fraud_claims"].sum()
    fraud_pct = 100 * fraud / claims
    top_sev = sev.loc[sev["fraud_pct"].idxmax()]
    top3 = state.nlargest(3, "total_amount")
    warnings = validation.query("severity == 'warn' and failed_rows > 0")
    full_weeks = week[(week["last_day"] - week["first_day"]).dt.days == 6]

    return [
        (
            "Summary",
            (
                f"{claims:,} auto claims totalling ${state['total_amount'].sum():,.0f}, "
                f"incidents {week['first_day'].min():%Y-%m-%d} to {week['last_day'].max():%Y-%m-%d}. "
                f"{fraud:,} claims ({fraud_pct:.1f}%) are labelled as fraud."
            ),
            None,
            None,
        ),
        (
            "Fraud by severity",
            f"Overall fraud rate is {fraud_pct:.1f}%.",
            ranked_bar(
                sev,
                "incident_severity",
                "fraud_pct",
                f"{top_sev['incident_severity']} claims are labelled fraud "
                f"{top_sev['fraud_pct']:.1f}% of the time vs {fraud_pct:.1f}% overall",
            ),
            sev,
        ),
        (
            "Fraud by incident type",
            "Collisions carry both the highest fraud rate and the highest average claim.",
            ranked_bar(
                kind, "incident_type", "fraud_pct", "Fraud rate (%) by incident type"
            ),
            kind,
        ),
        (
            "Claim cost by state",
            "Share of total claim cost by incident state.",
            ranked_bar(
                state,
                "incident_state",
                "total_amount",
                f"{', '.join(top3['incident_state'])} account for "
                f"{top3['pct_of_total_amount'].sum():.0f}% of claim cost",
            ),
            state,
        ),
        (
            "Weekly claim volume",
            "Weeks start on Monday. The chart leaves out partial weeks; the table shows every week.",
            px.line(
                full_weeks,
                x="week_start",
                y="claims",
                markers=True,
                title="Weekly claim volume (full weeks only)",
            ).update_layout(yaxis_rangemode="tozero"),
            week,
        ),
        (
            "Data quality",
            (
                f"All error checks passed. {len(warnings)} warning checks flagged rows "
                "that were kept for review."
            ),
            None,
            validation,
        ),
        (
            "Caveats",
            (
                "Source: public Kaggle dataset (buntyshah/auto-insurance-claims-data) of unknown origin, "
                "so results illustrate the pipeline rather than a real portfolio. "
                "Only two months of incidents, so no seasonality can be read. "
                "'Fraud' is the dataset's fraud_reported label, not a proven outcome, "
                "and the patterns above are correlations, not causes."
            ),
            None,
            None,
        ),
    ]


if __name__ == "__main__":
    with duckdb.connect(DB_PATH, read_only=True) as con:
        validation = con.sql("SELECT * FROM validation_report").df()
    raise_on_errors(validation)  # never report on data that failed validation
    sections = build_sections(run_queries(QUERIES), validation)
    path = save_html(
        build_html("Auto Insurance Claims Report", sections), "insurance_claims_report"
    )
    print(f"Report saved to {path}")
