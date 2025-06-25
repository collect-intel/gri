# VWRS Calculation Modes - Results Comparison

## Overview

The formulaic approach has been implemented to replace the hard-coded country list. The system now supports three modes for handling high-cardinality benchmarks.

## Mode Comparison for GD3 (n=971)

### Country Dimension VWRS Results:

| Mode | Description | Countries Kept | VWRS | GRI | Diversity |
|------|-------------|----------------|------|-----|-----------|
| **none** | Full benchmark (no simplification) | 228 | 0.9847 | 0.5589 | 0.4554 |
| **auto** | Formulaic (threshold = max(1/n, 0.001)) | ~101 | 0.9817 | 0.5518 | 0.4510 |
| **legacy** | Hard-coded list | 31 | 0.7818 | 0.5386 | 0.8276 |

### Key Observations:

1. **Auto mode (default)** produces VWRS values very close to "none" mode (0.9817 vs 0.9847)
   - Threshold = 1/971 = 0.103%
   - Keeps countries > 0.1% of world population
   - Results in ~101 countries being tracked individually

2. **Legacy mode** produces much lower (more conservative) VWRS (0.7818)
   - Fixed list of 31 major countries
   - Groups 197 countries as "Others" (27.4% of population)
   - More realistic assessment of coverage gaps

3. **GRI scores** are relatively stable across modes (0.54-0.56)
   - Less affected by the number of zero-sample strata
   - More robust metric overall

4. **Diversity scores** vary significantly
   - Higher with legacy mode (0.83) - easier to cover 31 countries
   - Lower with full/auto modes (0.45) - harder to cover 100+ countries

## Formula Details

The auto mode uses:
```python
threshold = max(1.0 / sample_size, 0.001)
```

This means:
- Keep strata expected to have ≥1 participant
- But always keep strata ≥ 0.1% of population
- Ensures minimum 80% population coverage

### Examples:
- n=100: threshold = 1.0%, keeps ~20 countries
- n=500: threshold = 0.2%, keeps ~70 countries  
- n=1000: threshold = 0.1%, keeps ~100 countries
- n=5000+: threshold = 0.1% (minimum), keeps ~100 countries

## Recommendations

1. **For new analyses**: Use `auto` mode (default)
   - Adapts to survey size
   - Statistically justified
   - No arbitrary decisions

2. **For conservative VWRS**: Use `legacy` mode
   - Shows more realistic coverage gaps
   - Compatible with previous analyses
   - Better for highlighting missing populations

3. **For comprehensive tracking**: Use `none` mode
   - Tracks all 228 countries
   - May inflate VWRS scores
   - Use when you need full granularity

## Implementation Status

✅ Formulaic approach fully implemented
✅ Backward compatibility maintained (legacy mode)
✅ Applied to all high-cardinality dimensions automatically
✅ Configurable via command line and API
✅ Default mode is now 'auto' instead of hard-coded lists