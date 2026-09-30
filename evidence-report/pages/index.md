---
title: Insurance Claims Report
sidebar_position: 1
---

```sql states
select distinct incident_state from claims.claims order by all
```

```sql incident_types
select distinct incident_type from claims.claims order by all
```

<Dropdown data={states} name=state value=incident_state title="State" multiple=true selectAllByDefault=true />
<Dropdown data={incident_types} name=incident_type value=incident_type title="Incident type" multiple=true selectAllByDefault=true />

```sql filtered
select *
from claims.claims
where incident_state in ${inputs.state.value}
    and incident_type in ${inputs.incident_type.value}
```

```sql selection
select count(*) as claims from ${filtered}
```

{#if selection.length && selection[0].claims == 0}

<Alert status=info>No claims match the selected filters.</Alert>

{:else}

```sql kpis
select
    count(*) as claims,
    sum(total_claim_amount) as total_amount,
    avg(fraud_reported::int) as fraud_rate,
    avg(total_claim_amount) as avg_claim,
    strftime(min(incident_date), '%b %-d, %Y') as first_date,
    strftime(max(incident_date), '%b %-d, %Y') as last_date
from ${filtered}
```

Claim volume, cost and reported fraud for auto insurance claims, built from the cleaned `claims` table of the analytics pipeline.
{#if kpis.length}Incidents from **{kpis[0].first_date}** to **{kpis[0].last_date}**.{/if}

<BigValue data={kpis} value=claims title="Total claims" fmt=num0 />
<BigValue data={kpis} value=total_amount title="Total claim amount" fmt=usd />
<BigValue data={kpis} value=fraud_rate title="Fraud rate" fmt=pct1 />
<BigValue data={kpis} value=avg_claim title="Average claim" fmt=usd0 />

## Trends

```sql daily
with days as (
    select unnest(generate_series(
        min(incident_date), max(incident_date), interval 1 day
    )) as day
    from ${filtered}
),
counts as (
    select incident_date as day, count(*) as claims
    from ${filtered}
    group by all
)
select
    days.day,
    coalesce(counts.claims, 0) as daily_claims,
    -- 2-week rolling average; empty until 14 days of data exist.
    case when row_number() over (order by days.day) >= 14
        then avg(coalesce(counts.claims, 0)) over (
            order by days.day rows between 13 preceding and current row
        )
    end as two_week_average
from days
left join counts using (day)
order by days.day
```

<LineChart
    data={daily}
    x=day
    y={['daily_claims', 'two_week_average']}
    yAxisTitle="Claims"
    title="Claims per day"
    subtitle="Daily count with a 2-week rolling average"
    colorPalette={['#a9c6e8', '#1f3a5f']}
/>

```sql weekly
select
    date_trunc('week', incident_date) as week_start,
    count(*) as claims,
    sum(total_claim_amount) as claim_cost,
    count(distinct incident_date) as days_with_data
from ${filtered}
group by all
order by week_start
```

<BarChart
    data={weekly}
    x=week_start
    y=claim_cost
    yFmt=usd
    title="Claim cost per week"
    subtitle="Weeks start on Monday; the first and last weeks are partial"
    colorPalette={['#1f3a5f']}
/>

```sql cost_split
select
    incident_type,
    sum(injury_claim) as injury,
    sum(property_claim) as property,
    sum(vehicle_claim) as vehicle
from ${filtered}
group by all
order by sum(total_claim_amount) desc
```

<BarChart
    data={cost_split}
    x=incident_type
    y={['vehicle', 'property', 'injury']}
    yFmt=usd
    swapXY=true
    title="Claim cost split by incident type"
    subtitle="Vehicle, property and injury parts add up to the total claim amount"
    colorPalette={['#1f3a5f', '#3d7cc9', '#a9c6e8']}
/>

{/if}
