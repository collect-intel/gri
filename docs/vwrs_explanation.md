# Understanding VWRS (Variance-Weighted Representativeness Score)

## What is VWRS?

VWRS is an improved version of the Global Representativeness Index (GRI) that accounts for statistical reliability when measuring how well a survey represents the global population.

## Key Differences from Traditional GRI

### Traditional GRI
- Treats all deviations equally
- Missing Luxembourg (0.001% of population) = same penalty as missing China (18%)
- Having 1 person vs 100 people from a country = same reliability

### VWRS 
- Weights deviations by statistical importance
- Small populations contribute less to error
- Large sample sizes are recognized as more reliable
- Can incorporate internal group consensus

## Two Types of VWRS

### 1. VWRS (Basic)
Only accounts for sampling reliability:
- **Standard Error**: `SE = sqrt(p(1-p)/n)`
- Small samples → high SE → less weight
- Missing countries → maximum SE → minimal weight

### 2. VWRS (With Internal Variance)
Also accounts for how much people within each group agree:
- Uses historical data on response variance within demographics
- **High consensus** (everyone agrees) → more reliable → more weight
- **High disagreement** (polarized opinions) → less reliable → less weight

## Example Results

| Metric | GD1 | GD2 | GD3 |
|--------|-----|-----|-----|
| Traditional GRI | 0.50 | 0.49 | 0.54 |
| VWRS (Basic) | 0.77 | 0.79 | 0.78 |
| VWRS (With Variance) | 0.77 | 0.79 | 0.78 |

## Interpretation

- **Traditional GRI ~0.50**: "This survey poorly represents the world"
- **VWRS ~0.78**: "This survey well represents the world, accounting for what's statistically achievable"

The large difference shows that traditional GRI is too harsh on global surveys where:
- Many small countries can't be sampled
- Sample sizes vary dramatically
- Perfect proportional representation is unrealistic

## When to Use Each

- **Traditional GRI**: When you need strict proportional representation
- **VWRS (Basic)**: When sample sizes vary and you want to account for reliability
- **VWRS (With Variance)**: When you also have data on internal group consensus

## Formula

```
VWRS = 1 - Σ(weight_i × |sample_prop_i - population_prop_i|) / Σ(weight_i)

where weight_i = population_prop_i × standard_error_i × reliability_i
```

This gives more weight to deviations that are:
- From large populations (high population_prop)
- Statistically uncertain (high standard_error)
- From internally consistent groups (high reliability)