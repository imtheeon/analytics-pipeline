-- Share of claims reported as fraud, per incident severity.
SELECT
    incident_severity,
    count(*) AS claims,
    count_if(fraud_reported)::INT AS fraud_claims,
    round(100.0 * avg(fraud_reported::INT), 1) AS fraud_pct,
    round(avg(total_claim_amount)) AS avg_amount
FROM claims
GROUP BY incident_severity
ORDER BY fraud_pct DESC;
