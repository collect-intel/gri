# GRI Python Module Documentation

The Global Representativeness Index (GRI) module provides tools for measuring how well survey samples represent global populations across demographic dimensions.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gri.git
cd gri

# Install dependencies
pip install -r requirements.txt

# Generate benchmark data (required before first use)
python scripts/process_data.py
```

## Quick Start

### Method 1: Using Individual Functions

Best for: Simple calculations, custom workflows, integration into existing code

```python
from gri import calculate_gri, load_data

# Load your data
survey_df = load_data('path/to/survey.csv')
benchmark_df = load_data('path/to/benchmark.csv')

# Calculate GRI score
gri_score = calculate_gri(survey_df, benchmark_df, ['country', 'gender', 'age_group'])
print(f"GRI Score: {gri_score:.4f}")
```

### Method 2: Using GRIAnalysis Class

Best for: Complete analysis workflows, multiple calculations, reports

```python
from gri import GRIAnalysis

# Create analysis from survey file
analysis = GRIAnalysis.from_survey_file('data/survey.csv')

# Calculate comprehensive scorecard
scorecard = analysis.calculate_scorecard(include_max_possible=True)

# Generate visualizations
analysis.plot_scorecard(save_to='results/scorecard.png')
analysis.plot_top_deviations('Country × Gender × Age', n=20)

# Generate text report
report = analysis.generate_report()
print(report)

# Export results
analysis.export_results(format='excel', filepath='results/gri_analysis.xlsx')
```

## Core Functions Reference

### Data Loading

```python
from gri import load_benchmark_suite, load_gd_survey

# Load all benchmark data at once
benchmarks = load_benchmark_suite()  # Returns dict of DataFrames

# Load Global Dialogues survey
survey = load_gd_survey('path/to/GD3_participants.csv')
```

### GRI Calculation

```python
from gri import calculate_gri, calculate_diversity_score

# Basic GRI calculation
gri = calculate_gri(survey_df, benchmark_df, dimension_columns)

# Diversity score (category coverage)
diversity = calculate_diversity_score(survey_df, benchmark_df, dimension_columns)

# Full scorecard with configuration
from gri import calculate_gri_scorecard
scorecard = calculate_gri_scorecard(
    survey_df, 
    benchmark_data,
    include_max_possible=True,
    n_simulations=1000
)
```

### Analysis Functions

```python
from gri import calculate_segment_deviations, identify_top_contributors

# Find which segments deviate most from benchmark
deviations = calculate_segment_deviations(survey_df, benchmark_df, ['country', 'gender'])

# Get top over/under-represented segments
top_over = identify_top_contributors(deviations, n=10, contribution_type='over')
top_under = identify_top_contributors(deviations, n=10, contribution_type='under')
```

### Visualization

```python
from gri import plot_gri_scorecard, plot_segment_deviations

# Create scorecard bar chart
plot_gri_scorecard(scorecard, title="Survey GRI Scores", save_path="scorecard.png")

# Show top deviations
plot_segment_deviations(deviations, top_n=20, save_path="deviations.png")
```

### Maximum Possible Scores

```python
from gri import calculate_max_possible_gri, monte_carlo_max_scores

# Quick calculation of maximum possible GRI
max_gri = calculate_max_possible_gri(benchmark_df, sample_size=1000)

# Detailed Monte Carlo simulation
max_results = monte_carlo_max_scores(
    benchmark_df, 
    sample_size=1000,
    n_simulations=1000
)
print(f"Max possible GRI: {max_results['max_gri']['mean']:.4f} ± {max_results['max_gri']['std']:.4f}")
```

## GRIAnalysis Class Reference

### Creating an Instance

```python
# From survey file
analysis = GRIAnalysis.from_survey_file('path/to/survey.csv', survey_type='gd')

# From DataFrame
analysis = GRIAnalysis(survey_df, benchmarks=benchmark_dict, survey_name="My Survey")
```

### Key Methods

| Method | Description | Example |
|--------|-------------|---------|
| `calculate_scorecard()` | Calculate GRI scores for all dimensions | `scorecard = analysis.calculate_scorecard(include_max_possible=True)` |
| `plot_scorecard()` | Create bar chart visualization | `analysis.plot_scorecard(save_to='scorecard.png')` |
| `plot_top_deviations()` | Show segments with largest gaps | `analysis.plot_top_deviations('Country × Gender × Age', n=20)` |
| `get_top_segments()` | Get DataFrame of top deviations | `top = analysis.get_top_segments('Country', n=10, segment_type='under')` |
| `generate_report()` | Create text report | `report = analysis.generate_report(include_analysis=True)` |
| `export_results()` | Export to CSV/JSON/Excel | `analysis.export_results('excel', 'results.xlsx')` |
| `check_alignment()` | Validate survey categories | `alignment = analysis.check_alignment()` |
| `print_summary()` | Quick console summary | `analysis.print_summary()` |

## Common Workflows

### 1. Basic GRI Calculation

```python
from gri import calculate_gri, load_data

survey = load_data('survey.csv')
benchmark = load_data('benchmark.csv')
score = calculate_gri(survey, benchmark, ['country', 'gender'])
```

### 2. Full Analysis with Visualizations

```python
from gri import GRIAnalysis

analysis = GRIAnalysis.from_survey_file('survey.csv')
analysis.calculate_scorecard(include_max_possible=True)
analysis.plot_scorecard(save_to='scorecard.png')
analysis.plot_top_deviations('Country × Gender × Age')
analysis.export_results('excel', 'full_analysis.xlsx')
```

### 3. Compare Multiple Surveys

```python
from gri import GRIAnalysis, create_comparison_plot

# Analyze each survey
surveys = {}
for survey_file in ['gd1.csv', 'gd2.csv', 'gd3.csv']:
    analysis = GRIAnalysis.from_survey_file(survey_file)
    surveys[survey_file] = analysis.calculate_scorecard()

# Create comparison visualization
create_comparison_plot(surveys, 'Country × Gender × Age', save_path='comparison.png')
```

### 4. Segment Analysis

```python
from gri import GRIAnalysis

analysis = GRIAnalysis.from_survey_file('survey.csv')

# Find under-represented segments
under_rep = analysis.get_top_segments(
    'Country × Gender × Age', 
    n=10, 
    segment_type='under'
)

print("Most under-represented segments:")
for _, segment in under_rep.iterrows():
    print(f"  {segment['segment_name']}: {segment['deviation']:.3f}")
```

## Troubleshooting

### Common Issues

1. **"Failed to load benchmark data"**
   - Run `python scripts/process_data.py` to generate benchmark files
   - Check that `data/processed/` directory exists

2. **"No module named 'gri'"**
   - Add the project root to your Python path
   - Or install as editable: `pip install -e .`

3. **Missing countries/categories**
   - Check `config/segments.yaml` for mappings
   - Some countries may lack benchmark data (see validation warnings)

4. **Memory issues with large surveys**
   - Process in chunks using `pd.read_csv(chunksize=...)`
   - Reduce Monte Carlo simulations for max scores

## Configuration

The module uses YAML configuration files in `config/`:

- `dimensions.yaml` - Defines all calculable dimensions
- `segments.yaml` - Maps survey categories to standard names
- `regions.yaml` - Geographic hierarchy definitions

## Performance Tips

- Pre-load benchmarks once and reuse: `benchmarks = load_benchmark_suite()`
- Cache GRIAnalysis instances when processing multiple operations
- Use `include_max_possible=False` for faster calculations
- Reduce `n_simulations` for quicker max score estimates

## Contributing

See the main repository README for contribution guidelines.