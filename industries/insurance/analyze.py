"""Run the insurance SQL queries on claims.duckdb and save the results to reports/."""

from pathlib import Path

from core.analyze import run_queries, save_results

QUERIES = Path(__file__).parent / "queries"

if __name__ == "__main__":
    results = run_queries(QUERIES)
    for name, df in results.items():
        print(f"\n== {name} ==\n{df.to_string(index=False)}")
    print(f"\nSaved {len(save_results(results))} results to reports/")
