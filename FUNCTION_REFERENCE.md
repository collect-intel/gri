# GRI Function Reference

## Core Functions

### `calculate_gri(survey_df, benchmark_df, strata_columns)`
Calculate the Global Representativeness Index score.

**Parameters:**
- `survey_df` (pd.DataFrame): Survey data with demographic columns
- `benchmark_df` (pd.DataFrame): Benchmark data with `population_proportion` column
- `strata_columns` (list): Column names defining the demographic strata

**Returns:**
- `float`: GRI score between 0 and 1

**Example:**
```python
gri_score = calculate_gri(survey, benchmark, ['country', 'gender', 'age_group'])
```

---

### `calculate_diversity_score(survey_df, benchmark_df, strata_columns)`
Calculate the diversity score (proportion of relevant strata represented).

**Parameters:**
- Same as `calculate_gri`

**Returns:**
- `float`: Diversity score between 0 and 1

---

### `load_benchmark_suite(data_dir='data/processed', dimensions=None)`
Load all benchmark data files at once.

**Parameters:**
- `data_dir` (str): Directory containing benchmark CSV files
- `dimensions` (list, optional): Specific dimensions to load

**Returns:**
- `dict`: Dictionary mapping dimension names to DataFrames

---

### `load_gd_survey(filepath, gd_version=None, config=None)`
Load Global Dialogues survey data with automatic format handling.

**Parameters:**
- `filepath` (str/Path): Path to GD participants CSV
- `gd_version` (int, optional): GD version (1-4), auto-detected if None
- `config` (GRIConfig, optional): Configuration object

**Returns:**
- `pd.DataFrame`: Processed survey data with standardized columns

---

### `calculate_segment_deviations(survey_df, benchmark_df, dimension_columns)`
Calculate how each segment deviates from benchmark proportions.

**Parameters:**
- `survey_df` (pd.DataFrame): Survey data
- `benchmark_df` (pd.DataFrame): Benchmark data
- `dimension_columns` (list): Columns defining the dimension

**Returns:**
- `pd.DataFrame`: Segments with deviation metrics

---

### `identify_top_contributors(deviations, n=10, contribution_type='both')`
Get segments that contribute most to representativeness gaps.

**Parameters:**
- `deviations` (pd.DataFrame): Output from `calculate_segment_deviations`
- `n` (int): Number of segments to return
- `contribution_type` (str): 'over', 'under', or 'both'

**Returns:**
- `pd.DataFrame`: Top contributing segments

---

### `plot_gri_scorecard(scores, title=None, figsize=(12,8), save_path=None)`
Create a bar chart visualization of GRI scores.

**Parameters:**
- `scores` (pd.DataFrame/dict): GRI scores by dimension
- `title` (str, optional): Plot title
- `figsize` (tuple): Figure size
- `save_path` (str/Path, optional): Where to save

**Returns:**
- `matplotlib.figure.Figure`: The plot figure

---

### `generate_text_report(scorecard, survey_name=None, include_analysis=True)`
Generate a comprehensive text report from GRI results.

**Parameters:**
- `scorecard` (pd.DataFrame/dict): GRI scorecard results
- `survey_name` (str, optional): Name for report header
- `include_analysis` (bool): Include detailed analysis section

**Returns:**
- `str`: Formatted text report

---

### `calculate_max_possible_gri(benchmark_df, sample_size, n_simulations=1000)`
Calculate the theoretical maximum GRI score for a given sample size.

**Parameters:**
- `benchmark_df` (pd.DataFrame): Benchmark data
- `sample_size` (int): Size of hypothetical sample
- `n_simulations` (int): Monte Carlo simulations

**Returns:**
- `float`: Expected maximum GRI score

---

## GRIAnalysis Class

### Constructor
```python
GRIAnalysis(survey_data, benchmarks=None, config=None, survey_name=None)
```

### Class Methods
```python
GRIAnalysis.from_survey_file(filepath, survey_type='gd', **kwargs)
```

### Instance Methods

#### `calculate_scorecard(dimensions='all', include_max_possible=False)`
Calculate GRI scores for specified dimensions.

#### `plot_scorecard(save_to=None, **kwargs)`
Create scorecard visualization.

#### `plot_top_deviations(dimension, n=20, save_to=None)`
Plot segments with largest deviations.

#### `get_top_segments(dimension, n=10, segment_type='both')`
Get DataFrame of top deviation segments.

#### `generate_report(output_file=None, include_analysis=True)`
Generate comprehensive text report.

#### `export_results(format='csv', filepath=None)`
Export results to CSV, JSON, or Excel.

#### `check_alignment()`
Validate survey categories against benchmarks.

#### `print_summary()`
Print analysis summary to console.

---

## Configuration Classes

### `GRIConfig(config_dir='config')`
Load and manage configuration from YAML files.

**Methods:**
- `get_all_dimensions()`: Get list of all configured dimensions
- `get_segment_mappings()`: Get category mappings
- `get_country_to_region_mapping()`: Get geographic hierarchy

---

## Utilities

### `aggregate_data(df, strata_columns)`
Aggregate survey data by demographic strata.

### `validate_survey_data(survey_df, required_columns=None)`
Check if survey data is valid for analysis.

### `check_category_alignment(survey_df, benchmark_df, columns)`
Check how well survey categories align with benchmark.

---

## Constants

### Dimension Names
Standard dimension names used throughout the module:
- `'Country × Gender × Age'`
- `'Country × Religion'` 
- `'Country × Environment'`
- `'Country'`
- `'Gender'`
- `'Age Group'`
- `'Religion'`
- `'Environment'`
- `'Region × Gender × Age'`
- `'Region × Religion'`
- `'Region × Environment'`
- `'Region'`
- `'Continent'`

### File Formats
Supported export formats:
- `'csv'`: Comma-separated values
- `'json'`: JSON with metadata
- `'excel'`: Excel workbook with multiple sheets