# analytics-pipeline

A small, reusable data pipeline in Python, pandas 3.0 and DuckDB:

```
load → clean → validate → store (DuckDB) → analyze (SQL) → report (HTML) → export (Power BI CSVs)
```

Generic steps live in `core/` and work on any CSV. Industry rules live in `industries/<name>/`.
The first industry is auto insurance claims.

## Results: auto insurance claims

1,000 claims totalling **$52.8M**, incidents from 2015-01-01 to 2015-03-01. **247 (24.7%)** are labelled as fraud.

**Fraud rate is highest for "Major Damage" claims: 60.5%, against 7–13% for every other severity.**

| Incident severity | Claims | Fraud claims | Fraud rate | Avg claim |
|---|---:|---:|---:|---:|
| Major Damage | 276 | 167 | 60.5% | $64,067 |
| Total Loss | 280 | 36 | 12.9% | $62,081 |
| Minor Damage | 354 | 38 | 10.7% | $48,643 |
| Trivial Damage | 90 | 6 | 6.7% | $5,302 |

**Collisions have both the highest fraud rate and the highest average claim.**

| Incident type | Claims | Fraud rate | Avg claim |
|---|---:|---:|---:|
| Single Vehicle Collision | 403 | 29.0% | $64,445 |
| Multi-vehicle Collision | 419 | 27.2% | $61,637 |
| Parked Car | 84 | 9.5% | $5,308 |
| Vehicle Theft | 94 | 8.5% | $5,517 |

- **By state:** NY, SC and WV account for 74% of total claim cost.
- **By week:** a steady 103–128 claims per full week, with no clear trend.
- **Data quality:** all 6 blocking checks pass. 2 claims are flagged and kept for review: a negative umbrella limit, and an incident dated before its policy started.

The full report with interactive charts is [`reports/insurance_claims_report.html`](reports/insurance_claims_report.html). Download it and open it in a browser, because GitHub shows HTML files as source code.

**Caveats:**
- This is a public Kaggle dataset of unknown origin, so the results show what the pipeline does rather than describe a real insurer.
- It covers only two months, so seasonality can't be measured.
- "Fraud" is the dataset's `fraud_reported` label, not a proven outcome, and all patterns are correlations.

## What each step does

| Step | Code | What it does |
|---|---|---|
| Load | `core/load.py` | Reads any CSV in `data/inbox/`. Treats `?` and blank cells as missing and parses date columns as dates. |
| Clean | `core/clean.py`, `industries/insurance/clean.py` | Renames columns to snake_case, trims spaces, fills known gaps, drops empty columns and duplicate rows, converts YES/NO to booleans, fixes typos. Saves Parquet. |
| Validate | `core/validate.py`, `industries/insurance/validate.py` | Runs rule-based checks. "error" rules stop the pipeline; "warn" rules flag rows and keep them. |
| Store | `core/store.py` | Writes `claims` and `validation_report` to `data/processed/claims.duckdb`. Re-running replaces the tables. |
| Analyze | `core/analyze.py`, `industries/insurance/queries/*.sql` | Runs every `.sql` file read-only and saves results to `reports/analysis_*.csv`. |
| Report | `core/report.py`, `industries/insurance/report.py` | Builds one HTML page with charts and tables. Refuses to run if validation failed. |
| Export | `core/export.py`, `industries/insurance/export.py` | Writes `claims_clean.csv` and one CSV per summary query to `reports/powerbi/` for Power BI (ISO dates, no index). Git-ignored. |

## Run it

Requirements:
- a conda env named `data-analysis` with Python 3.12, pandas 3, duckdb, pyarrow, plotly, pytest and ruff
- the raw data: download the dataset (see [DATA_SOURCES.md](DATA_SOURCES.md)) and put `insurance_claims.csv` in `data/inbox/`

Run the whole pipeline with one command. It stops at the first step that fails:

```bash
conda run -n data-analysis python -m industries.insurance.run_pipeline
```

Or run the steps one at a time:

```bash
conda run -n data-analysis python -m industries.insurance.clean
conda run -n data-analysis python -m industries.insurance.validate
conda run -n data-analysis python -m industries.insurance.store
conda run -n data-analysis python -m industries.insurance.analyze
conda run -n data-analysis python -m industries.insurance.report
conda run -n data-analysis python -m industries.insurance.export
```

Open the interactive dashboard. It reads `data/processed/claims.duckdb`, so run the pipeline first:

```bash
conda run --no-capture-output -n data-analysis streamlit run dashboard.py
```

It shows KPI cards and five tabs, all filterable by state and incident type in the sidebar:

- **Overview:** fraud share (donut), claim amount distribution (box plot), claim cost split into injury, property and vehicle (stacked bar)
- **Fraud:** fraud rate by severity and by incident type, plus an incident type × severity heatmap
- **Geography:** claim cost by state, with a per-state table
- **Trends:** claims per day with a 2-week rolling average
- **Insights:** written findings, trends, what to watch and caveats, all computed from the filtered data

The theme lives in `.streamlit/config.toml`.

There is also a static [Evidence](https://evidence.dev) report in `evidence-report/`, with four pages: Overview (KPIs and trends), Fraud (by severity, incident type and a heatmap), Geography (by state) and Insights (written findings and caveats calculated in SQL). Every page has State and Incident type filters. It uses the open-source Evidence framework (`@evidence-dev/evidence` 40), which reads `data/processed/claims.duckdb` directly. It needs Node.js 18+. Run the pipeline first, then:

```bash
cd evidence-report
npm install
npm run sources
npm run dev
```

`npm run sources` copies the claims table into the report, so run it again after the pipeline changes the data. `npm run dev` opens the report at http://localhost:3000. For a static site in `evidence-report/build/`, run `npm run build`. Anonymous usage stats are turned off in `evidence.settings.json`.

Run the tests and the linter:

```bash
conda run -n data-analysis pytest
conda run -n data-analysis ruff check .
```

## Data and license

The source is [Auto Insurance Claims Data](https://www.kaggle.com/datasets/buntyshah/auto-insurance-claims-data) on Kaggle. Its license is listed as *Unknown*, so the raw data is not included in this repo; only code and summary results are. See [DATA_SOURCES.md](DATA_SOURCES.md).
