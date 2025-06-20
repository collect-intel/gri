# Demographic Variance Analysis Summary

## Overview
This analysis examined response variance across all poll questions in GD1-GD3 surveys to understand which demographic groups have higher internal consensus vs. higher diversity of opinions.

## Key Findings

### 1. Overall Consensus Patterns
- **Highest consensus dimensions** (less variance within groups):
  - Environment (Urban/Rural): ~96-97% consensus
  - Continent: ~93-97% consensus  
  - Region: ~93-96% consensus
  - Religion: ~93-96% consensus

- **Lowest consensus dimensions** (more variance within groups):
  - Country × Gender × Age: ~91-93% consensus
  - Country × Religion: ~92-93% consensus
  - Age Groups: ~92-95% consensus

### 2. Variance Trends Across Surveys
- GD1 → GD2: Slight increase in consensus (reduced variance)
- GD2 → GD3: Slight decrease in consensus for granular dimensions
- Most stable: Geographic groupings (continent, region)
- Most variable: Fine-grained demographic intersections

### 3. Country-Specific Insights (from GD3)
**High consensus countries** (can sample less):
- China: 94.6% consensus
- India: 94.1% consensus  
- Pakistan: 94.1% consensus
- Bangladesh: 93.3% consensus

**Low consensus countries** (need oversampling):
- Denmark: 89.9% consensus
- Hungary: 91.8% consensus
- Italy: 92.1% consensus
- Netherlands: 92.4% consensus

### 4. Optimal Allocation Recommendations

#### For Country-level sampling (N=1,000):
- **Efficiency gain**: 17.1% reduction in sampling error
- **Oversample**: USA (+50%), Ethiopia (+53%), smaller countries (+51%)
- **Undersample**: China (-46%), Pakistan (-43%), India (-42%)

#### For Age Groups (N=1,000):
- **Efficiency gain**: 3.1% reduction in sampling error
- **Oversample**: 65+ (+40%), 56-65 (+22%)
- **Undersample**: 26-35 (-16%), 18-25 (-12%)

#### For Gender:
- Minimal efficiency gains (<1%)
- Near-proportional allocation is optimal

### 5. Practical Implications

1. **Geographic diversity matters more than size**: Small countries with diverse opinions need more samples than large homogeneous countries.

2. **Age extremes need attention**: Both youngest and oldest groups show more variance and benefit from oversampling.

3. **Simple demographics (gender, urban/rural) are well-behaved**: These show high consensus and can use proportional sampling.

4. **Intersection effects are significant**: Country × Gender × Age combinations show much more variance than individual dimensions.

## Recommendations for Future Surveys

1. **Use variance-weighted allocation** for country sampling to achieve 15-20% efficiency gains

2. **Maintain proportional sampling** for gender and urban/rural splits

3. **Consider oversampling** older age groups (65+) and Western countries with higher response diversity

4. **Track variance trends** across surveys to detect changes in demographic consensus

## Data Files Generated
- Variance scores by dimension: `GD[1-3]_*_variance.csv`
- Variance lookup tables: `GD[1-3]_variance_lookup.json`
- Cross-survey comparison: `cross_gd_variance_comparison.csv`
- Optimal allocation comparisons: `optimal_allocation/` directory