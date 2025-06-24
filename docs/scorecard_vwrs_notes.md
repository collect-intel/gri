# GRI Scorecard VWRS Implementation Notes

## Overview
The GRI scorecard implementation includes support for both full and simplified country benchmarks, which significantly affects VWRS (Variance-Weighted Representativeness Score) calculations.

## Full vs Simplified Benchmarks

### Full Benchmark (Default)
- Uses all 228 countries from UN population data
- Many countries have 0 samples in typical surveys
- Results in higher VWRS values (0.98+ for GD3)
- More accurate for global population coverage

### Simplified Benchmark (Optional)
- Uses 31 major countries representing ~72% of global population
- Remaining ~28% grouped as "Others"
- Results in more conservative VWRS values (~0.78 for GD3)
- Better for comparing with simplified analyses

## Usage

### Command Line
```bash
# Generate scorecard with full benchmarks (default)
python scripts/generate_gd_scorecards.py --gd 3

# Generate scorecard with simplified benchmarks
python scripts/generate_gd_scorecards.py --gd 3 --simplified
```

### Makefile
```bash
# Full benchmarks
make scorecard GD=3

# Simplified benchmarks
make scorecard GD=3 SIMPLIFIED=1
```

### Python API
```python
from gri import GRIScorecard

scorecard_gen = GRIScorecard()

# Full benchmarks
scorecard_df = scorecard_gen.generate_scorecard(
    survey_df, base_path, gd_num=3, 
    use_simplified_benchmarks=False  # Default
)

# Simplified benchmarks
scorecard_df = scorecard_gen.generate_scorecard(
    survey_df, base_path, gd_num=3,
    use_simplified_benchmarks=True
)
```

## VWRS Calculation Details

The VWRS calculation is sensitive to the number of strata because:

1. **Standard Error Impact**: Strata with 0 samples have maximum standard error (1.0)
2. **Weighting**: Each stratum is weighted by `population_proportion × standard_error × reliability`
3. **Many Zero Strata**: With 228 countries, most have 0 samples, but still contribute small weights
4. **Net Effect**: More strata with 0 samples → higher overall VWRS

### Example for GD3:
- **Full benchmark (228 countries)**: VWRS = 0.9847
- **Simplified benchmark (31 countries + Others)**: VWRS = 0.7818

## Recommendations

1. **For Published Results**: Use full benchmarks to show comprehensive global coverage
2. **For Conservative Analysis**: Use simplified benchmarks to focus on major population centers
3. **For Comparisons**: Ensure consistent benchmark choice across analyses
4. **For Reporting**: Always specify which benchmark was used

## Implementation Details

The simplified benchmark includes:
- China (18.0%)
- India (17.5%)
- United States (4.2%)
- Indonesia (3.5%)
- Pakistan (2.8%)
- Brazil (2.7%)
- Nigeria (2.6%)
- Bangladesh (2.1%)
- Russian Federation (1.8%)
- Mexico (1.6%)
- ... and 21 more countries
- Others (remaining ~28%)

This matches the benchmark used in `examples/representativeness_comparison.py` for consistency.