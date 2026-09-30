---
title: Geography
sidebar_position: 3
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

```sql by_state
select
    incident_state,
    count(*) as claims,
    sum(total_claim_amount) as claim_cost,
    sum(total_claim_amount) / sum(sum(total_claim_amount)) over () as cost_share,
    avg(total_claim_amount) as avg_claim,
    avg(fraud_reported::int) as fraud_rate
from ${filtered}
group by all
order by claim_cost desc
```

```sql summary
select
    arg_max(incident_state, claim_cost) as top_state,
    format('{:,}', arg_max(claims, claim_cost)) as top_claims,
    format('{:.0f}%', 100 * max(cost_share)) as top_share,
    arg_min(incident_state, claims) as small_state,
    min(claims) as small_claims
from ${by_state}
```

{#if summary.length}

**{summary[0].top_state}** has the most claim cost: {summary[0].top_claims} claims and {summary[0].top_share} of the total.
The smallest state, **{summary[0].small_state}**, has only {summary[0].small_claims} claims, so treat its rates with caution.

{/if}

<Grid cols=2>
    <BarChart
        data={by_state}
        x=incident_state
        y=claim_cost
        yFmt=usd
        swapXY=true
        labels=true
        title="Claim cost by state"
        colorPalette={['#1f3a5f']}
    />
    <BarChart
        data={by_state}
        x=incident_state
        y=fraud_rate
        yFmt=pct0
        swapXY=true
        labels=true
        title="Fraud rate by state"
        colorPalette={['#3d7cc9']}
    />
</Grid>

<DataTable data={by_state} rows=all>
    <Column id=incident_state title="State" />
    <Column id=claims title="Claims" fmt=num0 />
    <Column id=claim_cost title="Claim cost" fmt=usd0 />
    <Column id=cost_share title="Share of cost" fmt=pct1 />
    <Column id=avg_claim title="Average claim" fmt=usd0 />
    <Column id=fraud_rate title="Fraud rate" fmt=pct1 contentType=colorscale />
</DataTable>

{/if}
