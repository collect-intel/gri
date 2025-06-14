# TASK_LIST: GRI Module Refactoring and Enhancement

## Overview
Transform GRI from a collection of scripts and notebooks into a streamlined, professional Python module that makes Global Representativeness Index calculations simple and accessible.

## Task 1: Modularize - Create a Clean, Professional GRI Module ✅ COMPLETED

### Objective
Create a properly structured Python module that reduces notebook code by 50-70% while making GRI calculations intuitive and powerful.

### New Module Structure ✅ COMPLETED
```
gri/
├── __init__.py          # Export main classes and functions ✅
├── calculator.py        # Keep core GRI calculations ✅
├── calculator_config.py # Keep config-aware calculations ✅
├── config.py           # Keep configuration management ✅
├── utils.py            # Enhanced utilities ✅
├── validation.py       # Data validation functions ✅
├── data_loader.py      # NEW: Unified data loading ✅
├── analysis.py         # NEW: Segment and deviation analysis ✅
├── visualization.py    # NEW: Standard plotting functions ✅
├── simulation.py       # NEW: Monte Carlo and max scores ✅
├── reports.py         # NEW: Report generation utilities ✅
└── analyzer.py         # NEW: GRIAnalysis class (was api.py) ✅
```

### Target API Design ✅ ACHIEVED
Users should be able to calculate GRI with minimal code:

```python
# Example 1: Simple GRI calculation ✅ WORKING
from gri import GRIAnalysis

analysis = GRIAnalysis.from_survey_file('data/gd3_participants.csv')
scorecard = analysis.calculate_scorecard(dimensions='all')
print(scorecard.summary())

# Example 2: With visualization ✅ WORKING
analysis.plot_scorecard(save_to='results/gd3_scorecard.png')
analysis.plot_top_deviations(n=10)

# Example 3: Compare multiple surveys ✅ POSSIBLE WITH FUNCTIONS
from gri import compare_surveys, create_comparison_plot
# Functions available for comparison workflows
```

### Key Functions to Extract and Consolidate ✅ ALL COMPLETED

#### From Notebooks:
1. **data_loader.py** ✅:
   - `load_benchmark_suite()` - Load all benchmark files at once ✅
   - `load_gd_survey(filepath, gd_version=None)` - Handle GD format quirks ✅
   - `load_wvs_survey(filepath, wave=None)` - Load World Values Survey data ⏳ (pending WVS integration)
   - `apply_segment_mappings(df, config)` - Apply mappings from segments.yaml ✅

2. **analysis.py** ✅:
   - `check_category_alignment(survey_df, benchmark_df, columns)` ✅
   - `calculate_segment_deviations(survey_df, benchmark_df, dimension)` ✅
   - `identify_top_contributors(deviations, n=10, type='over')` ✅
   - `generate_alignment_report(survey_df, benchmarks)` ✅

3. **visualization.py** ✅:
   - `plot_gri_scorecard(scores, title=None, figsize=(12, 8))` ✅
   - `plot_sample_distribution(survey_df, dimension, benchmark_df=None)` ✅
   - `plot_diversity_coverage(diversity_scores)` ✅
   - `plot_segment_deviations(deviations, top_n=20)` ✅

#### From Scripts:
4. **simulation.py** (from calculate_max_possible_scores.py) ✅:
   - `generate_optimal_sample(benchmark_df, sample_size, dimension)` ✅
   - `monte_carlo_max_scores(benchmark_df, sample_size, n_simulations=1000)` ✅
   - `calculate_max_possible_gri(benchmark_df, sample_size, dimension)` ✅
   - `calculate_efficiency_ratio(actual_score, max_possible_score)` ✅

5. **reports.py** ✅:
   - `generate_text_report(scorecard, include_analysis=True)` ✅
   - `export_results(scorecard, format='csv', filepath=None)` ✅
   - `create_summary_statistics(survey_df, benchmark_df)` ✅

### Implementation Requirements ✅ ALL COMPLETED
- Use type hints throughout ✅
- Add comprehensive docstrings with examples ✅
- Follow numpy/scipy docstring conventions ✅
- Maintain backwards compatibility where possible ✅
- Add __all__ exports to control public API ✅

## Task 2: Integrate Maximum Possible Scores ✅ COMPLETED

### Objective
Seamlessly integrate maximum possible score calculations into the main GRI workflow.

### Implementation Details ✅ ALL COMPLETED

1. **Enhance scorecard output** to include: ✅
   ```python
   {
       'dimension': 'Country × Gender × Age',
       'gri_score': 0.8234,
       'max_possible_score': 0.9156,  # NEW
       'efficiency_ratio': 0.899,      # NEW (actual/max)
       'sample_size': 1000,
       'diversity_score': 0.945,
       'max_possible_diversity': 0.978, # NEW
       'diversity_efficiency': 0.966    # NEW
   }
   ```

2. **Make it configurable**: ✅
   ```python
   scorecard = analysis.calculate_scorecard(
       dimensions='all',
       include_max_possible=True,  # Default: False
       n_simulations=1000         # For Monte Carlo
   )
   ```

3. **Update command-line interface**: ✅
   - Integrated into calculator_config.py
   - Available through GRIAnalysis class

4. **Visualization updates**: ✅
   - Efficiency ratio shown in reports
   - Available in plot_gri_scorecard function
   - Can be extended with additional visualization options

### Output Format ✅ IMPLEMENTED
When displaying results, show:
```
Country × Gender × Age:
  GRI Score: 0.823 (89.9% of maximum possible 0.915)
  Diversity: 0.945 (96.6% of maximum possible 0.978)
```

## Task 3: Add World Values Survey (WVS) Integration

### Data Requirements

1. **Data Location**: 
   - Add WVS data files to `data/raw/survey_data/wvs/`
   - Expected files: `WVS_Wave6.csv`, `WVS_Wave7.csv`

2. **Preprocessing Steps**:
   - Create `scripts/process_wvs_survey.py` similar to `process_gd_survey.py`
   - Map WVS variable codes to GRI standard names
   - Handle WVS-specific formats (numeric codes, weights)

3. **Segment Mappings**:
   - Extend `segments.yaml` with WVS section (already has placeholder)
   - Map numeric codes to text values
   - Handle WVS-specific categories

4. **Notebook Updates**:
   - Load both WVS Wave 6 and Wave 7
   - Calculate GRI scores for each
   - Create comparison visualizations:
     - Side-by-side score comparisons
     - Trend analysis GD1→GD2→GD3 vs WVS6→WVS7
     - Sample size and coverage differences

### Expected Analysis
- Compare representativeness between GD (purposive sampling) and WVS (probability sampling)
- Identify which dimensions show biggest differences
- Discuss implications for global survey design

## Task 4: Complete GRI Calculation Example Notebook

### Required Sections for "Top Contributing Segments Analysis"

1. **Deviation Analysis**:
   ```python
   # Calculate which segments contribute most to non-representativeness
   deviations = analysis.calculate_segment_deviations('Country × Gender × Age')
   
   # Show top 10 over-represented segments
   over_rep = analysis.get_top_segments(deviations, n=10, type='over')
   analysis.plot_segment_deviations(over_rep, title="Most Over-represented Groups")
   
   # Show top 10 under-represented segments
   under_rep = analysis.get_top_segments(deviations, n=10, type='under')
   analysis.plot_segment_deviations(under_rep, title="Most Under-represented Groups")
   ```

2. **Impact Analysis**:
   - Calculate how much GRI would improve by fixing top deviations
   - Show "what-if" scenarios for rebalancing

3. **Recommendations Section**:
   - Generate automated recommendations for improving representativeness
   - Prioritize based on impact and feasibility

4. **Summary Visualizations**:
   - Heatmap of deviations by country/demographic
   - Scatter plot of segment size vs deviation
   - Cumulative impact chart

### Notebook Structure
- Keep demonstration concise (target: 200-300 lines total)
- Focus on showcasing module capabilities
- Include clear markdown explanations
- End with actionable insights

## Success Criteria

### Code Quality Metrics
- [x] Notebooks reduced by 50-70% in line count ✅
- [x] No duplicated functions across files ✅
- [x] All functions have type hints and docstrings ✅
- [x] Module can be imported without path manipulation ✅
- [x] Comprehensive test coverage with 90 tests ✅

### Functionality Metrics
- [x] GRI calculation takes < 1 second for 10,000 participants ✅
- [x] Visualizations are publication-ready by default ✅
- [x] Max possible scores add < 10% to computation time ✅
- [x] All existing notebooks still run successfully ✅

### User Experience Metrics
- [x] New user can calculate GRI in < 10 lines of code ✅
- [x] Clear error messages for common issues ✅
- [x] Comprehensive examples in docstrings ✅
- [x] Intuitive function and parameter names ✅

## Implementation Order

1. **Phase 1**: Create core modules (data_loader, analysis, visualization) ✅ COMPLETED
2. **Phase 2**: Integrate max possible scores into calculator ✅ COMPLETED
3. **Phase 3**: Update all notebooks to use new module structure ✅ COMPLETED
4. **Phase 4**: Add WVS data processing and comparison ✅ COMPLETED
5. **Phase 5**: Polish, document, and add examples ✅ COMPLETED

🎉 **ALL PHASES COMPLETED**

## Testing Requirements ✅ COMPLETED

- ✅ Added `tests/` directory with pytest unit tests
- ✅ Created comprehensive test suite (90 tests total)
- ✅ All tests passing (100% pass rate)
- ✅ Edge case handling included (empty data, missing categories, etc.)
- ✅ Validated against known GRI calculations

## Documentation Standards ✅ COMPLETED

- README.md with quick start guide ✅
- Function reference documentation ✅ (FUNCTION_REFERENCE.md)
- Example gallery with common use cases ✅ (examples/ directory)
- Module documentation with usage guide ✅ (gri/README.md)

## Questions Resolved ✅

1. **Installation**: Make pip-installable with setup.py ✅
2. **Dependencies**: Keep minimal (pandas, numpy, matplotlib, pyyaml) ✅
3. **Backwards compatibility**: Maintain where possible, document breaking changes ✅
4. **Performance**: Optimize for datasets up to 100k participants ✅

## Summary of Completed Work

### ✅ Task 1: Module Creation - COMPLETED
- ✅ Created all new module files (data_loader, analysis, visualization, simulation, reports, analyzer)
- ✅ Integrated all functions with type hints and comprehensive docstrings
- ✅ Created GRIAnalysis class for high-level workflow management
- ✅ Module is pip-installable with setup.py
- ✅ Added comprehensive test suite with 90 tests (all passing)

### ✅ Task 2: Maximum Possible Scores - COMPLETED
- Integrated into calculate_gri_scorecard with include_max_possible parameter
- Added efficiency ratio calculations
- Monte Carlo simulations available through simulation.py
- Configurable through GRIAnalysis class

### ✅ Task 3: WVS Integration - COMPLETED
- ✅ Created process_wvs_survey.py script to handle WVS data processing
- ✅ Successfully processed WVS Wave 6 (85,219 participants from 57 countries)
- ✅ Successfully processed WVS Wave 7 (62,927 participants from 71 countries)
- ✅ Added load_wvs_survey() function to data_loader module
- ✅ Created comprehensive comparison notebook (notebook 6)
- ✅ Added WVS integration tests
- ✅ Updated module exports to include WVS functionality

### ✅ Task 4: Complete Notebook 2 - COMPLETED
- ✅ Added top segments analysis section
- ✅ Demonstrated new module capabilities
- ✅ Updated all notebooks to use new module structure

### ✅ Documentation - COMPLETED
- Comprehensive module documentation in gri/README.md
- Function reference in FUNCTION_REFERENCE.md
- Example scripts in examples/ directory
- Updated main README.md with new installation instructions

### ✅ Notebook Updates - COMPLETED
- **Notebook 1 (Data Preparation)**: Reduced by ~75% using load_benchmark_suite() and load_gd_survey()
- **Notebook 2 (GRI Calculation)**: Reduced by ~70%, added Top Contributing Segments Analysis
- **Notebook 3 (Advanced Analysis)**: Reduced by ~60%, integrated Monte Carlo and comparison features
- **Notebook 4 (Coarse Dimensions)**: Removed ~500 lines of manual mapping code
- **Notebook 5 (Survey Comparison)**: Reduced from ~300 to ~50 lines using built-in comparison features