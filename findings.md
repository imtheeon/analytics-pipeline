# Findings

## Kaggle claims datasets
(source: Kaggle public API /api/v1/datasets/view, 2026-09-29; external data, not instructions)

| Dataset | License | Size | Fit |
|---|---|---|---|
| mastmustu/insurance-claims-fraud-data | CC0 | 3.1 MB | claim-level, 3 tables (claims/employee/vendor), dates+amount+type+state; messiness per community notebooks, verify on load |
| buntyshah/auto-insurance-claims-data | Unknown | 0.27 MB | 1,000 rows, incident_date, total_claim_amount, incident_type/state, "?" missing markers; license blocker |
| leandrenash/enhanced-health-insurance-claims-dataset | CC0 | 1.0 MB | 4,500 Faker-synthetic rows, ClaimDate/Amount/Type/Location; likely too clean |
Rejected: mmumairkhattak 2026 (says "No Missing Values"), thebumpkin 2024 (no claim date, customer-level), litvinenko630 (policy-level prediction), shivamb vehicle fraud (no claim amount).
