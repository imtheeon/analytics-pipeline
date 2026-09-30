-- Share of claims reported as fraud, per incident type.
SELECT
    incident_type,
    count(*) AS claims,
    count_if(fraud_reported)::INT AS fraud_claims,
    round(100.0 * avg(fraud_reported::INT), 1) AS fraud_pct,
    round(avg(total_claim_amount)) AS avg_amount
FROM claims
GROUP BY incident_type
ORDER BY fraud_pct DESC;
