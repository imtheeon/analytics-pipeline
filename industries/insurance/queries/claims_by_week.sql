-- Weekly claim volume and cost; first_day/last_day show which weeks are partial.
SELECT
    date_trunc('week', incident_date)::DATE AS week_start,
    min(incident_date)::DATE AS first_day,
    max(incident_date)::DATE AS last_day,
    count(*) AS claims,
    sum(total_claim_amount)::BIGINT AS total_amount,
    round(avg(total_claim_amount)) AS avg_amount
FROM claims
GROUP BY week_start
ORDER BY week_start;
