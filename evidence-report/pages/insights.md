---
title: Insights
sidebar_position: 4
---

Every number below is calculated from the claims data when the report is built.

<!-- Numbers are formatted in SQL and inserted with {query[0].column}: the Value
component adds a trailing space, which breaks punctuation right after a number. -->

```sql facts
select
    format('{:,}', count(*)) as claims,
    format('{:,}', count_if(fraud_reported)) as fraud_claims,
    format('{:.1f}%', 100 * avg(fraud_reported::int)) as fraud_rate,
    strftime(min(incident_date), '%b %-d') as first_date,
    strftime(max(incident_date), '%b %-d, %Y') as last_date,
    datediff('day', min(incident_date), max(incident_date)) + 1 as days,
    format('{:.1f}', (datediff('day', min(incident_date), max(incident_date)) + 1) / 30.0) as months
from claims.claims
```

```sql top_severity
select
    incident_severity,
    format('{:.1f}%', 100 * avg(fraud_reported::int)) as fraud_rate,
    count_if(fraud_reported) as fraud_claims,
    count(*) as claims
from claims.claims
group by all
order by avg(fraud_reported::int) desc
limit 1
```

```sql top_type
select
    incident_type,
    '$' || format('{:,}', round(avg(total_claim_amount))::bigint) as avg_claim,
    format('{:.0f}%', 100 * sum(total_claim_amount) / sum(sum(total_claim_amount)) over ()) as cost_share
from claims.claims
group by all
order by avg(total_claim_amount) desc
limit 1
```

```sql top_state
select
    incident_state,
    format('{:.0f}%', 100 * sum(total_claim_amount) / sum(sum(total_claim_amount)) over ()) as cost_share,
    format('{:.1f}%', 100 * avg(fraud_reported::int)) as fraud_rate
from claims.claims
group by all
order by sum(total_claim_amount) desc
limit 1
```

```sql trend
with days as (
    select unnest(generate_series(
        min(incident_date), max(incident_date), interval 1 day
    )) as day
    from claims.claims
),
counts as (
    select incident_date as day, count(*) as claims
    from claims.claims
    group by all
),
daily as (
    select
        coalesce(counts.claims, 0) as claims,
        row_number() over (order by days.day) as day_number,
        count(*) over () as total_days
    from days
    left join counts using (day)
),
halves as (
    select
        avg(claims) filter (where day_number <= total_days / 2) as first_half,
        avg(claims) filter (where day_number > total_days / 2) as second_half
    from daily
)
select
    format('{:.1f}', first_half) as first_half,
    format('{:.1f}', second_half) as second_half,
    second_half >= first_half as rose,
    format('{:.1f}', abs(second_half - first_half)) as change
from halves
```

```sql watch
select
    incident_type,
    incident_severity,
    count(*) as claims,
    format('{:.0f}%', 100 * avg(fraud_reported::int)) as fraud_rate
from claims.claims
group by all
having count(*) >= 20
order by avg(fraud_reported::int) desc
limit 1
```

## Key findings

- **{top_severity[0].incident_severity}** claims have the highest fraud rate at {top_severity[0].fraud_rate} ({top_severity[0].fraud_claims} of {top_severity[0].claims}), versus {facts[0].fraud_rate} across all {facts[0].claims} claims.
- **{top_type[0].incident_type}** claims cost the most on average ({top_type[0].avg_claim}) and make up {top_type[0].cost_share} of total claim cost.
- **{top_state[0].incident_state}** accounts for the largest share of claim cost ({top_state[0].cost_share}), with a fraud rate of {top_state[0].fraud_rate}.

## Trends

- Claims averaged {trend[0].first_half} per day in the first half of the period and {trend[0].second_half} in the second half, {#if trend[0].rose}a rise{:else}a drop{/if} of {trend[0].change} per day.

## What to watch next

{#if watch.length > 0}

- **{watch[0].incident_type}** claims with **{watch[0].incident_severity}**: {watch[0].fraud_rate} of {watch[0].claims} are flagged as fraud, the highest of any combination with 20+ claims. These deserve a closer look in the next review.

{:else}

- No incident type and severity combination has 20+ claims, so none is singled out.

{/if}

## Caveats

<Alert status=warning>

- The data covers only {facts[0].days} days ({facts[0].first_date} to {facts[0].last_date}, about {facts[0].months} months), too short for a reliable forecast or any seasonal pattern.
- "Fraud" is the dataset's `fraud_reported` label ({facts[0].fraud_claims} of {facts[0].claims} claims), not proof of fraud. Every pattern here is a correlation.

</Alert>
