-- Weekly claim volume and cost (data covers 2015-01-01 to 2015-03-01; first/last weeks are partial).
SELECT
    date_trunc('week', incident_date)::DATE AS week_start,
    count(*) AS claims,
    sum(total_claim_amount)::BIGINT AS total_amount,
    round(avg(total_claim_amount)) AS avg_amount
FROM claims
GROUP BY week_start
ORDER BY week_start;
