# Representativeness Metrics Comparison

This document compares three approaches to measuring survey representativeness:
1. **GRI** (Global Representativeness Index)
2. **SRI** (Strategic Representativeness Index)  
3. **VWRS** (Variance-Weighted Representativeness Score)

## Quick Comparison

| Metric | Target | Best For | GD3 Score |
|--------|--------|----------|-----------|
| GRI | Proportional representation | Demographic mirroring | 0.54 |
| SRI | Strategic allocation (√prop) | Minimizing uncertainty | 0.55 |
| VWRS | Reliability-weighted | Realistic assessment | 0.78 |

## Traditional GRI

**Formula**: `GRI = 1 - 0.5 × Σ|sample_prop - population_prop|`

**Characteristics**:
- Perfect score (1.0) = exact proportional representation
- All deviations penalized equally
- Missing tiny country = same penalty as missing large country

**Use when**:
- You need strict demographic matching
- All groups are equally important regardless of size
- You have resources to sample small populations

## Strategic Representativeness Index (SRI)

**Formula**: `SRI = 1 - 0.5 × Σ|sample_prop - strategic_target|`

Where strategic target = `√(population_prop) / Σ√(population_prop)`

**Characteristics**:
- Perfect score (1.0) = optimal allocation for uncertainty reduction
- Small groups get boosted (but not to equality)
- Balances information gain across all groups

**Use when**:
- You want to minimize total survey uncertainty
- You're designing future sample allocation
- Small groups need reliable estimates

### Example Strategic Boosts
- 0.1% population → 3.2x boost (0.1% → 0.32%)
- 1% population → 3.2x boost (1% → 3.2%)  
- 10% population → 1.0x (no change)
- 40% population → 0.63x reduction (40% → 25%)

## Variance-Weighted Representativeness Score (VWRS)

**Formula**: `VWRS = 1 - Σ(weight × |sample_prop - population_prop|) / Σ(weight)`

Where weight = `population_prop × standard_error × reliability`

**Characteristics**:
- Accounts for sampling reliability (standard error)
- Can incorporate within-group consensus
- Small/unreliable samples contribute less to score

**Use when**:
- Sample sizes vary dramatically
- You want realistic assessment of representation
- Perfect proportional sampling is unachievable

## Practical Example (GD Surveys)

| Country | Population | GD3 Sample | GRI Impact | SRI Target | VWRS Weight |
|---------|------------|------------|------------|------------|-------------|
| China | 18.0% | 7.1% | High penalty | 12.7% | Low (reliable n=70) |
| Denmark | 0.1% | 0.2% | Low penalty | 0.7% | Minimal (unreliable n=2) |
| Missing small | 0.1% | 0% | Low penalty | 0.7% | Minimal (max uncertainty) |

## Which Metric to Use?

### Use GRI when:
- Regulatory compliance requires proportional representation
- You have large, well-funded surveys
- Every demographic group must be heard equally

### Use SRI when:
- Planning future survey design
- Budget constraints require smart allocation
- You need reliable estimates for all groups

### Use VWRS when:
- Evaluating existing survey data
- Sample sizes vary by orders of magnitude
- You want credit for what's statistically achievable

## Implementation

All three metrics are available in the GRI package:

```python
from gri.calculator import calculate_gri
from gri.strategic_index import calculate_sri_from_dataframes
from gri.variance_weighted import calculate_vwrs_from_dataframes

# Calculate all three
gri = calculate_gri(survey_df, benchmark_df, ['country'])
sri, sri_details = calculate_sri_from_dataframes(survey_df, benchmark_df, ['country'])
vwrs, vwrs_details = calculate_vwrs_from_dataframes(survey_df, benchmark_df, ['country'])
```

## Key Takeaway

These metrics answer different questions:
- **GRI**: "How proportional is our sample?"
- **SRI**: "How well-designed is our sample for minimizing uncertainty?"
- **VWRS**: "How representative is our sample, accounting for what's realistic?"

For global surveys with many small countries, VWRS typically gives the most realistic assessment, while SRI provides the best guidance for future sampling.