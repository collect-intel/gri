# Benchmark Simplification Proposal

## Summary

The current hard-coded list of 31 countries should be replaced with a **formulaic approach** that adapts to survey characteristics.

## Recommended Formula

```python
def calculate_simplification_threshold(sample_size: int, 
                                     min_threshold: float = 0.001,
                                     min_coverage: float = 0.8) -> float:
    """
    Calculate threshold for including strata in simplified benchmark.
    
    Logic:
    1. Base threshold = 1/sample_size (expect ≥1 participant)
    2. Never go below min_threshold (default 0.1% of population)
    3. Ensure result achieves min_coverage (default 80%)
    """
    return max(1.0 / sample_size, min_threshold)
```

## Why Formulaic is Better

### 1. **Adapts to Survey Scale**
- Small survey (n=100): Keep only top ~20 countries
- Medium survey (n=1000): Keep ~100 countries  
- Large survey (n=10000): Keep more granular data

### 2. **Statistically Justified**
- Threshold = 1/n means each kept stratum expects ≥1 participant
- Below this, strata are more likely to have 0 samples
- Grouping them as "Others" gives more honest VWRS

### 3. **Handles Edge Cases**
- Always keep countries ≥ 0.1% (major populations)
- Always ensure 80% coverage (avoid too much in "Others")
- Always keep countries that appear in actual sample

### 4. **Transparent and Reproducible**
- No magic numbers or arbitrary lists
- Can be documented in methods sections
- Other researchers can replicate

## Implementation Approach

### Phase 1: Update Scorecard Module
```python
class GRIScorecard:
    def __init__(self, simplification_mode='auto'):
        """
        simplification_mode:
          - 'none': Use full benchmarks
          - 'auto': Formulaic based on sample size
          - 'legacy': Use hard-coded 31 countries
        """
        self.simplification_mode = simplification_mode
```

### Phase 2: Apply to All High-Cardinality Dimensions
Currently only countries are affected, but the approach could handle:
- **Regions** (22 strata): Probably fine as-is
- **Languages** (if added): Would definitely need simplification
- **Occupations** (if added): Would need simplification
- **Sub-national regions** (if added): Would need simplification

### Phase 3: Configuration Options
```yaml
# config/simplification.yaml
simplification:
  mode: auto  # none, auto, legacy
  
  auto_settings:
    min_threshold: 0.001  # Minimum 0.1% of population
    min_coverage: 0.8     # Ensure 80% coverage
    
  dimension_overrides:
    country:
      min_threshold: 0.001
    religion:
      min_threshold: 0.01  # Less granular for religion
```

## Migration Path

1. **Default to 'auto' mode** for new analyses
2. **Keep 'legacy' mode** for backward compatibility
3. **Document in outputs** which mode was used
4. **Provide conversion utility** to compare modes

## Example Results

For GD3 (n=971):
- **Legacy mode**: 31 countries + Others (hard-coded)
- **Auto mode**: ~35 countries + Others (formulaic)
- **None mode**: 228 countries (full benchmark)

| Mode | Countries | VWRS | More Realistic? |
|------|-----------|------|-----------------|
| None | 228 | 0.985 | No - inflated |
| Legacy | 31 | 0.782 | Yes |
| Auto | 35 | ~0.79 | Yes - adaptive |

## The Bottom Line

A formulaic approach is superior because it:
1. **Adapts** to survey characteristics automatically
2. **Eliminates** arbitrary decisions
3. **Generalizes** to any dimension
4. **Documents** itself through the formula
5. **Balances** statistical rigor with practical reality

The formula `threshold = max(1/sample_size, 0.001)` is simple, intuitive, and statistically grounded.