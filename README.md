# Global Representativeness Index (GRI)

The Global Representativeness Index (GRI) is a tool for measuring how well a sample of people represents the global population across various demographic dimensions. It provides a standardized score that can be used to assess and compare the representativeness of different surveys or datasets. This is crucial for ensuring that research findings and data-driven insights are not skewed by a sample that is imbalanced relative to the world's actual population distribution.

## Why GRI?

In an increasingly interconnected world, it is essential to gather data that reflects the diversity of the global population. However, collecting a perfectly representative sample is a significant challenge. The GRI provides a quantitative measure to:

* **Assess Sample Quality:** Objectively evaluate how well a survey sample mirrors the global population across key demographics.
* **Identify Gaps:** Pinpoint specific demographic strata that are over-or under-represented in a sample.
* **Improve Data Collection:** Inform future data collection efforts to target under-represented groups and improve sample balance.
* **Standardize Evaluation:** Offer a consistent metric to compare the representativeness of different studies or datasets over time.

## How GRI is Calculated

The GRI is calculated based on the **Total Variation Distance (TVD)**, a statistical measure of the difference between two probability distributions. In this case, it compares the distribution of the survey sample to the true distribution of the global population.

### The Formula

Let $I$ be the set of all possible strata, where each stratum $i \in I$ represents a unique combination of demographic segments within a specific country (e.g., "Men 18-25 in Nigeria").

Let:
* $q_i$ be the true proportion of the total global population in stratum $i$.
* $s_i$ be the proportion of the total sample in stratum $i$.

The Global Representativeness Index (GRI) is calculated as:

$$
GRI = 1 - \frac{1}{2} \sum_{i \in I} |s_i - q_i|
$$

**Explanation:**

* $|s_i - q_i|$: This calculates the absolute difference between the sample proportion and the true population proportion for each stratum.
* $\sum_{i \in I} |s_i - q_i|$: This sums the absolute differences across all strata.
* $\frac{1}{2} \sum_{i \in I} |s_i - q_i|$: This is the Total Variation Distance, which is normalized to a scale of 0 to 1. A value of 0 means the sample is perfectly representative, and a value of 1 means the sample and population distributions are completely disjoint.
* $1 - \text{TVD}$: The final GRI score is inverted so that **a higher score indicates better representativeness**. A score of 1 would mean perfect representativeness, and a score of 0 would indicate a complete lack of representativeness.

### GRI Scorecard

The GRI can be calculated for any demographic dimension or combination of strata. For a comprehensive assessment, we recommend a **GRI Scorecard** that evaluates representativeness across several key dimensions:

* **Country x Gender x Age**
* **Country x Religion**
* **Country x Environment (Urban/Rural)**

An **Average GRI** from this scorecard can be used as a standalone metric to describe the overall representativeness of a sample.

### Diversity Score (Coverage Rate)

In addition to the GRI, which measures the proportional match, the **Diversity Score** measures the breadth of coverage of the sample. It calculates the percentage of relevant strata (with a population proportion $q_i$ above a certain threshold $X$) that are actually represented in the sample (i.e., have at least one participant).

Let:
* $X$ be a pre-defined threshold for the population proportion $q_i$. Only consider strata $i$ where $q_i > X$ as "relevant" for this diversity score (to avoid penalizing for exceedingly small strata). By default, we choose $X = \frac{1}{2N}$, where $N$ is the sample size, representing an expected count of 0.5 participants (rounding up to 1 participant).

Using indicator functions, where $\mathbf{1}(\text{condition})$ is 1 if the condition is true, and 0 otherwise:

$$\text{DiversityScore} = \frac{\text{NumRepresentedStrata}}{\text{NumRelevantStrata}} = \frac{\sum_{i \in I} \mathbf{1}(s_i > 0 \text{ AND } q_i > X)}{\sum_{i \in I} \mathbf{1}(q_i > X)}$$

This formula ensures that:
- **Relevant strata**: Only demographic strata with meaningful population proportions are considered
- **Dynamic threshold**: The relevance threshold adapts to sample size - larger samples can represent smaller population segments
- **Coverage focus**: The score measures breadth of representation, not proportional accuracy

## Data Sources

Calculating the GRI requires reliable benchmark data for the global population. The following sources are recommended for demographic data:

* **Age and Gender:**
    * United Nations, Department of Economic and Social Affairs, Population Division. (2023). *World Population Prospects 2022*.
* **Urban/Rural Distribution:**
    * United Nations, Department of Economic and Social Affairs, Population Division. (2018). *World Urbanization Prospects: The 2018 Revision*.
* **Religion:**
    * Pew Research Center. (2012). *The Global Religious Landscape*.

This repository provides tools to calculate the GRI and Diversity Score for any survey, given the survey data and the corresponding global population benchmarks.

## Getting Started

### Quick Start (5 minutes)

The fastest way to get started with GRI is using our automated setup:

```bash
# Clone the repository
git clone https://github.com/your-org/gri.git
cd gri

# One-command setup and demo
make setup
make demo
```

This will:
1. Create a virtual environment
2. Install all dependencies 
3. Process benchmark data from UN and Pew Research
4. Run a demonstration with sample survey data
5. Show you a complete GRI Scorecard

### Installation Options

#### Option 1: Install as Python Package (Recommended)
```bash
# Clone and install the GRI module
git clone https://github.com/your-org/gri.git
cd gri
pip install -e .

# Process benchmark data (required first time)
python scripts/process_data.py
```

#### Option 2: Use with Make Commands
```bash
# Clone the repository
git clone https://github.com/your-org/gri.git
cd gri

# Setup with Make
make setup
```

### Prerequisites

- **Python 3.8+** 
- **Git** (for cloning the repository)
- **10 GB disk space** (for benchmark data processing)

### Step-by-Step Setup

#### 1. Environment Setup
```bash
# Option A: Using Make
make venv
make install

# Option B: Using pip directly
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# Verify setup
make health-check
```

#### 2. Process Benchmark Data
```bash
# Process UN and Pew Research data into GRI format
make process-data
# OR
python scripts/process_data.py

# Verify data processing
make validate-data

# View data summary
make show-benchmarks
```

#### 3. Calculate Your First GRI
```bash
# Run demonstration with sample data
make calculate-gri
```

You'll see output like:
```
GRI Scorecard Results:
  Country × Gender × Age:  GRI=0.2345, Diversity=0.8901
  Country × Religion:      GRI=0.1234, Diversity=0.7654
  Country × Environment:   GRI=0.3456, Diversity=0.5432

Average GRI: 0.2345
Assessment: Moderate representativeness
```

### Using GRI with Your Data

#### Basic Usage - Functional API

```python
from gri import calculate_gri, calculate_diversity_score, load_data
import pandas as pd

# Load your survey data (CSV with demographic columns)
survey_data = pd.read_csv('your_survey.csv')

# Load processed benchmark data
benchmark = load_data('data/processed/benchmark_country_gender_age.csv')

# Calculate GRI score
gri_score = calculate_gri(
    survey_data, 
    benchmark, 
    strata_cols=['country', 'gender', 'age_group']
)

print(f"GRI Score: {gri_score:.4f}")
```

#### Basic Usage - GRIAnalysis Class (Recommended for Full Workflow)

```python
from gri import GRIAnalysis

# Create analysis from your survey file
analysis = GRIAnalysis.from_survey_file('your_survey.csv')

# Calculate comprehensive scorecard
scorecard = analysis.calculate_scorecard(include_max_possible=True)

# Generate visualizations
analysis.plot_scorecard(save_to='gri_scorecard.png')

# Generate text report
report = analysis.generate_report()
print(report)

# Export results
analysis.export_results(format='excel', filepath='gri_results.xlsx')
```

#### Required Data Format

Your survey data should be a CSV with these columns:

| Column | Description | Example Values |
|--------|-------------|----------------|
| `country` | Country name | "United States", "India", "Brazil" |
| `gender` | Gender identity | "Male", "Female" |
| `age_group` | Age bracket | "18-25", "26-35", "36-45", "46-55", "56-65", "65+" |
| `religion` | Religious affiliation | "Christianity", "Islam", "Hinduism", "Buddhism", "Judaism", "I do not identify with any religious group or faith", "Other religious group" |
| `environment` | Location type | "Urban", "Rural" |

#### Complete GRI Scorecard

For a comprehensive assessment, calculate GRI across all three dimensions:

```python
from gri import calculate_gri, load_data

# Load benchmark data for all dimensions
benchmark_age_gender = load_data('data/processed/benchmark_country_gender_age.csv')
benchmark_religion = load_data('data/processed/benchmark_country_religion.csv')  
benchmark_environment = load_data('data/processed/benchmark_country_environment.csv')

# Calculate GRI for each dimension
gri_age_gender = calculate_gri(survey_data, benchmark_age_gender, 
                              ['country', 'gender', 'age_group'])
gri_religion = calculate_gri(survey_data, benchmark_religion, 
                            ['country', 'religion'])
gri_environment = calculate_gri(survey_data, benchmark_environment, 
                               ['country', 'environment'])

# Calculate average GRI
average_gri = (gri_age_gender + gri_religion + gri_environment) / 3
print(f"Average GRI: {average_gri:.4f}")
```

### Learning Path

#### 1. **Start Here**: Run the Demo
```bash
make demo
```

#### 2. **Explore Examples**: Jupyter Notebooks
```bash
# Execute all example notebooks
make run-notebooks

# Or manually open individual notebooks:
jupyter notebook notebooks/1-data-preparation.ipynb
jupyter notebook notebooks/2-gri-calculation-example.ipynb  
jupyter notebook notebooks/3-advanced-analysis.ipynb
```

#### 3. **Understand the Data**: View Benchmarks
```bash
make show-benchmarks
```

#### 4. **Advanced Analysis**: Gap Identification
The advanced notebook (`3-advanced-analysis.ipynb`) shows you how to:
- Identify which demographic groups are over/under-represented
- Generate actionable recommendations for improving sample balance
- Compare surveys over time or across methodologies

### Interpreting GRI Scores

| GRI Score | Interpretation |
|-----------|----------------|
| 0.8 - 1.0 | **Excellent** representativeness |
| 0.6 - 0.8 | **Good** representativeness |
| 0.4 - 0.6 | **Moderate** representativeness |
| 0.0 - 0.4 | **Poor** representativeness |

**Diversity Score** measures coverage breadth (0.0 = no relevant strata covered, 1.0 = all relevant strata covered).

### Common Use Cases

- **Survey Quality Assessment**: Evaluate how well your sample represents the global population
- **Recruitment Optimization**: Identify which demographic groups to target for better balance
- **Research Validation**: Provide quantitative evidence of sample representativeness in publications
- **Comparative Analysis**: Compare representativeness across studies, time periods, or methodologies
- **Real-time Monitoring**: Track representativeness during data collection to course-correct

### Getting Help

- **Module Documentation**: See `gri/README.md` for comprehensive module usage guide
- **Function Reference**: See `FUNCTION_REFERENCE.md` for complete function and class documentation
- **Examples**: Check the `notebooks/` directory for detailed examples, plus `examples/` for Python scripts
- **Function Docstrings**: See inline documentation in `gri/` module files
- **Issues**: Report bugs or request features on GitHub
- **Makefile Commands**: Run `make help` for all available commands

### Development and Testing

```bash
# Run test suite
make test

# Code quality checks
make lint
make format

# Clean up
make clean
```

## Development Note

The Jupyter notebooks in this repository include executed outputs for demonstration purposes. This provides immediate value for new users who can see complete examples with results, visualizations, and analysis without needing to run the code.

If you're contributing code changes that affect the notebooks, please run `make run-notebooks` after your changes to update the documentation with fresh outputs.
