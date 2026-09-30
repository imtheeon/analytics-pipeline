-- Claim volume and cost per incident state, with each state's share of total cost.
SELECT
    incident_state,
    count(*) AS claims,
    sum(total_claim_amount)::BIGINT AS total_amount,
    round(avg(total_claim_amount)) AS avg_amount,
    round(100.0 * sum(total_claim_amount) / sum(sum(total_claim_amount)) OVER (), 1) AS pct_of_total_amount
FROM claims
GROUP BY incident_state
ORDER BY total_amount DESC;
