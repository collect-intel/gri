# Representativeness Metrics Comparison

This document compares the approaches to measuring survey representativeness in the GRI framework:
1. **GRI** (Global Representativeness Index)
2. **SRI** (Strategic Representativeness Index)
3. **Design Effect / Effective N** (Inferential cost measurement)

## Quick Comparison

| Metric | Purpose | Best For | Example (GD3 Country) |
|--------|---------|----------|-----------------------|
| GRI | Demographic distance | Measuring representation quality | 0.54 |
| SRI | Allocation strategy | Survey design guidance | 0.55 |
| Design Effect | Precision cost | Understanding inferential consequence | d_eff = 3.0 |
| Effective N | Usable sample size | Interpreting statistical power | N_eff = 330 |

## Global Representativeness Index (GRI)

**Formula**: `GRI = 1 - 0.5 × Σ|sample_prop - population_prop|`

**Characteristics**:
- Perfect score (1.0) = exact proportional representation
- Built on Total Variation Distance, a well-understood metric
- All deviations penalized proportionally

**Use when**:
- You need a standardized representativeness measure
- Comparing surveys across time or across programs
- Reporting the demographic distance between sample and population

## Strategic Representativeness Index (SRI)

**Formula**: `SRI = 1 - 0.5 × Σ|sample_prop - strategic_target|`

Where strategic target = `√(population_prop) / Σ√(population_prop)`

**Characteristics**:
- Perfect score (1.0) = optimal allocation for uncertainty reduction
- Small groups get boosted (but not to equality)
- Balances information gain across all groups

**Use when**:
- Planning future survey design
- Budget constraints require smart allocation
- Small groups need reliable estimates

### Example Strategic Boosts
- 0.1% population → 3.2x boost (0.1% → 0.32%)
- 1% population → 3.2x boost (1% → 3.2%)
- 10% population → 1.0x (no change)
- 40% population → 0.63x reduction (40% → 25%)

## Design Effect and Effective Sample Size

**Formula**: `d_eff = Σ(q_norm² / p_i)` over represented strata

Where `q_norm` is the population proportion renormalized over strata present in the sample.

**Effective N**: `N_eff = N / d_eff`

**Precision Retained**: `1 / d_eff`

**Characteristics**:
- Quantifies the variance inflation from post-stratification reweighting
- d_eff = 1.0 means perfect allocation (no precision loss)
- d_eff = 3.0 means the survey has the precision of N/3 optimally allocated respondents
- Based on standard survey methodology (Kish design effect)

**Use when**:
- You need to know the actual statistical power of your survey
- Communicating the inferential cost of demographic mismatch
- Deciding whether to invest in better recruitment vs. larger samples

## Which Metric to Use?

These metrics answer different questions:

- **GRI**: "How closely does our sample match the population?" (distance)
- **SRI**: "How well-designed is our sample for minimizing uncertainty?" (design quality)
- **Design Effect**: "What is the precision cost of our demographic mismatch?" (inferential consequence)
- **Effective N**: "What is our survey actually worth in statistical power?" (usable sample)

**Recommended reporting**: Report GRI + Effective N together. GRI tells stakeholders the representativeness quality; Effective N translates the cost into a concrete, intuitive number.

## Implementation

```python
from gri import calculate_gri, calculate_sri, calculate_design_effect

# GRI: representativeness distance
gri = calculate_gri(survey_df, benchmark_df, ['country', 'gender', 'age_group'])

# SRI: strategic allocation quality
sri = calculate_sri(survey_df, benchmark_df, ['country', 'gender', 'age_group'])

# Design effect: precision cost
result = calculate_design_effect(survey_df, benchmark_df, ['country', 'gender', 'age_group'])
print(f"Design Effect: {result['design_effect']:.2f}")
print(f"Effective N: {result['effective_n']:.0f}")
print(f"Precision Retained: {result['precision_retention']:.1%}")
```

For a complete analysis across all dimensions, use the `GRIScorecard` class which calculates all metrics automatically.
