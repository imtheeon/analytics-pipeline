---
title: Fraud
sidebar_position: 2
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

"Fraud" here means the dataset's `fraud_reported` label, not a proven outcome.

```sql fraud_kpis
select
    count_if(fraud_reported) as fraud_claims,
    avg(fraud_reported::int) as fraud_rate,
    avg(total_claim_amount) filter (where fraud_reported) as avg_fraud_claim,
    avg(total_claim_amount) filter (where not fraud_reported) as avg_other_claim,
    avg(total_claim_amount) filter (where fraud_reported)
        / avg(total_claim_amount) filter (where not fraud_reported) - 1 as fraud_premium
from ${filtered}
```

<BigValue data={fraud_kpis} value=fraud_claims title="Claims flagged as fraud" fmt=num0 />
<BigValue data={fraud_kpis} value=fraud_rate title="Fraud rate" fmt=pct1 />
<BigValue
    data={fraud_kpis}
    value=avg_fraud_claim
    title="Average flagged claim"
    fmt=usd0
    comparison=fraud_premium
    comparisonFmt=pct0
    comparisonTitle="vs. unflagged claims"
    downIsGood=true
/>

## By severity and incident type

```sql by_severity
select
    incident_severity,
    count(*) as claims,
    avg(fraud_reported::int) as fraud_rate
from ${filtered}
group by all
order by fraud_rate desc
```

```sql by_type
select
    incident_type,
    count(*) as claims,
    avg(fraud_reported::int) as fraud_rate
from ${filtered}
group by all
order by fraud_rate desc
```

<Grid cols=2>
    <BarChart
        data={by_severity}
        x=incident_severity
        y=fraud_rate
        yFmt=pct0
        swapXY=true
        labels=true
        title="Fraud rate by severity"
        colorPalette={['#1f3a5f']}
    />
    <BarChart
        data={by_type}
        x=incident_type
        y=fraud_rate
        yFmt=pct0
        swapXY=true
        labels=true
        title="Fraud rate by incident type"
        colorPalette={['#3d7cc9']}
    />
</Grid>

## Incident type × severity

```sql combos
select
    incident_type,
    incident_severity,
    case incident_severity
        when 'Trivial Damage' then 1
        when 'Minor Damage' then 2
        when 'Major Damage' then 3
        else 4
    end as severity_order,
    count(*) as claims,
    avg(fraud_reported::int) as fraud_rate
from ${filtered}
group by all
order by severity_order, incident_type
```

<Heatmap
    data={combos}
    x=incident_severity
    y=incident_type
    value=fraud_rate
    valueFmt=pct0
    xSort=severity_order
    title="Fraud rate by incident type and severity"
    subtitle="A dash means no claims with that combination"
/>

<DataTable data={combos} rows=all>
    <Column id=incident_type title="Incident type" />
    <Column id=incident_severity title="Severity" />
    <Column id=claims title="Claims" fmt=num0 />
    <Column id=fraud_rate title="Fraud rate" fmt=pct1 contentType=colorscale />
</DataTable>

{/if}
