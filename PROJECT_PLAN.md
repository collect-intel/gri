# Project Plan: Global Representativeness Index (GRI)

This document outlines the step-by-step implementation plan for the `gri` Python project. Follow these tasks sequentially to build the repository.

## Guiding Principles

- **Modularity:** Keep functions and modules focused on a single responsibility.
- **Clarity:** Code should be well-documented with docstrings and comments.
- **Robustness:** The implementation should handle edge cases like missing data or empty strata.
- **Reproducibility:** The data processing and analysis pipeline should be fully reproducible through the provided scripts and notebooks.

---

## Task 1: Initialize Project Structure

Create the following directory and file structure. Files can be empty initially.

```
gri/
├── .gitignore
├── Readme.md
├── LICENSE
├── data/
│   ├── raw/
│   │   ├── benchmark_data/
│   │   └── survey_data/
│   └── processed/
├── notebooks/
│   ├── 1-data-preparation.ipynb
│   ├── 2-gri-calculation-example.ipynb
│   └── 3-advanced-analysis.ipynb
├── scripts/
│   ├── download_benchmarks.py
│   └── process_data.py
├── gri/
│   ├── __init__.py
│   ├── calculator.py
│   └── utils.py
└── tests/
    ├── test_calculator.py
    └── test_utils.py
```
- For `.gitignore`, add standard Python entries (e.g., `__pycache__/`, `*.pyc`, `.env`, `venv/`).
- The `Readme.md` file has been provided separately. You can create a placeholder for now.

---

## Task 2: Implement Core Calculation Logic

In the file `gri/calculator.py`, implement the core functions for calculating the GRI and Diversity Score. Use the `pandas` library for data manipulation.

**File: `gri/calculator.py`**

```python
import pandas as pd
from typing import List

def calculate_gri(survey_df: pd.DataFrame, benchmark_df: pd.DataFrame, strata_cols: List[str]) -> float:
    """
    Calculates the Global Representativeness Index (GRI).

    The GRI is a measure of how well a sample's distribution matches a benchmark
    population distribution across a set of demographic strata.
    GRI = 1 - Total Variation Distance (TVD)
    TVD = 0.5 * sum(|sample_proportion - benchmark_proportion|)

    Args:
        survey_df (pd.DataFrame): DataFrame with survey participant data. Each row
                                  should represent one participant.
        benchmark_df (pd.DataFrame): DataFrame with true population proportions.
                                     Must contain the strata_cols and a column named
                                     'population_proportion' (qi).
        strata_cols (List[str]): A list of column names that define the strata.

    Returns:
        float: The GRI score, ranging from 0.0 (complete mismatch) to 1.0 (perfect match).
    """
    # 1. Calculate sample proportions (s_i) for each stratum.
    #    - Group survey_df by strata_cols and count participants in each group.
    #    - Divide the count for each group by the total number of survey participants.
    #    - This creates a Series or DataFrame with strata as the index and 'sample_proportion' as the values.
    # 2. Prepare the benchmark proportions (q_i).
    #    - The benchmark_df should already contain the 'population_proportion' column.
    # 3. Merge sample and benchmark proportions.
    #    - Perform an outer merge on the strata columns to ensure all strata from both
    #      the sample and the benchmark are included.
    #    - Fill any resulting NaN values in both proportion columns with 0. This handles
    #      strata present in one dataset but not the other.
    # 4. Calculate Total Variation Distance (TVD).
    #    - Compute the sum of the absolute differences between the sample and benchmark proportions.
    #    - Multiply the sum by 0.5.
    # 5. Calculate and return the GRI.
    #    - GRI = 1 - TVD
    pass

def calculate_diversity_score(survey_df: pd.DataFrame, benchmark_df: pd.DataFrame, strata_cols: List[str], population_threshold: float = 0.00001) -> float:
    """
    Calculates the Diversity Score (strata coverage rate).

    This score measures the percentage of relevant benchmark strata that are
    represented in the survey sample.

    Args:
        survey_df (pd.DataFrame): DataFrame with survey participant data.
        benchmark_df (pd.DataFrame): DataFrame with true population proportions.
        strata_cols (List[str]): List of column names that define the strata.
        population_threshold (float): The minimum population proportion for a stratum
                                      to be considered 'relevant'. Defaults to 0.00001.

    Returns:
        float: The Diversity Score, from 0.0 to 1.0.
    """
    # 1. Identify unique strata present in the survey sample.
    #    - Drop duplicate rows in survey_df based on strata_cols.
    # 2. Identify relevant strata from the benchmark data.
    #    - Filter benchmark_df to include only rows where 'population_proportion' > population_threshold.
    # 3. Calculate the number of relevant strata.
    #    - If this number is zero, return 1.0 as there are no relevant strata to miss.
    # 4. Calculate how many of the relevant strata are present in the sample.
    #    - Perform an inner merge between the unique sample strata and the relevant benchmark strata.
    #    - The number of rows in the resulting DataFrame is the count of covered strata.
    # 5. Calculate the score.
    #    - score = (count of covered strata) / (count of relevant strata)
    pass
```

---

## Task 3: Implement Utility Functions

In `gri/utils.py`, create helper functions for data handling.

**File: `gri/utils.py`**

```python
import pandas as pd

def load_data(filepath: str, **kwargs) -> pd.DataFrame:
    """Loads data from a specified file path into a pandas DataFrame."""
    # Implement loading for CSV files using pd.read_csv.
    # Pass along any additional keyword arguments to the pandas function.
    # Include error handling for FileNotFoundError.
    pass

def aggregate_data(df: pd.DataFrame, strata_cols: list[str]) -> pd.DataFrame:
    """Aggregates a DataFrame to count occurrences in each stratum."""
    # Group the DataFrame by the strata_cols.
    # Calculate the size of each group and reset the index.
    # Rename the resulting size column to 'count'.
    # Return a DataFrame with strata_cols and a 'count' column.
    pass
```

---

## Task 4: Write Unit Tests

In `tests/test_calculator.py`, create unit tests using the `pytest` framework to verify the correctness of the calculation logic.

**File: `tests/test_calculator.py`**

- Create several test functions with sample `survey_df` and `benchmark_df` DataFrames created using `pd.DataFrame`.
- **`test_gri_perfect_match`**: Create a sample where `survey_df` proportions are identical to `benchmark_df`. The GRI should be `1.0`.
- **`test_gri_complete_mismatch`**: Create a sample where `survey_df` and `benchmark_df` have no overlapping strata. The GRI should be `0.0`.
- **`test_gri_partial_match`**: Create a realistic scenario with some differences. Calculate the expected GRI manually and assert that the function's output is approximately equal to the expected value.
- **`test_gri_empty_survey`**: Test that if `survey_df` is empty, the GRI is `0.0`.
- **`test_diversity_score`**: Test the `calculate_diversity_score` function with known inputs and expected outputs for full coverage, partial coverage, and zero coverage.
- Test edge cases, such as when one DataFrame has strata not present in the other.

---

## Task 5: Create Data Processing Scripts

Implement the scripts for acquiring and processing the benchmark data.

**File: `scripts/download_benchmarks.py`**

- Use libraries like `requests` and `urllib` to download the population data files from their public sources. Add comments indicating the source URLs.
- Save the raw files into `data/raw/benchmark_data/`.

**File: `scripts/process_data.py`**

- Load the raw data files from `data/raw/benchmark_data/`.
- Clean and transform the data. This will involve significant data manipulation using pandas to align countries, age buckets, and other categories.
- The objective is to generate final, processed benchmark files.
- The script should generate separate benchmark CSVs for each GRI Scorecard dimension:
    - `benchmark_country_gender_age.csv`
    - `benchmark_country_religion.csv`
    - `benchmark_country_environment.csv`
- Each file must contain the relevant strata columns and a `population_proportion` column, where the sum of proportions is 1.0.
- Save the processed files to `data/processed/`.

---

## Task 6: Create Example Notebooks

Develop a series of Jupyter Notebooks in the `notebooks/` directory to demonstrate the full workflow. Assume a Git submodule containing participant data is available at `data/raw/survey_data/global_dialogues/`.

**Notebook: `1-data-preparation.ipynb`**

- Provide markdown instructions on how to run the `scripts/download_benchmarks.py` and `scripts/process_data.py` scripts first.
- Show how to load a sample survey dataset (e.g., `data/raw/survey_data/global_dialogues/GD4_participant.csv`).
- Demonstrate necessary cleaning steps for the survey data (e.g., standardizing column names, mapping values to match benchmark categories).

**Notebook: `2-gri-calculation-example.ipynb`**

- Load the processed benchmark data (e.g., `data/processed/benchmark_country_gender_age.csv`) and the cleaned survey data.
- Import the `calculate_gri` and `calculate_diversity_score` functions from the `gri` module.
- Demonstrate calculating the GRI for each of the three scorecard dimensions.
- Calculate the Average GRI across the three scores.
- Calculate the Diversity Score for each dimension.
- Use libraries like `matplotlib` or `seaborn` to create simple visualizations of the results (e.g., a bar chart showing the GRI scores).

**Notebook: `3-advanced-analysis.ipynb`**

- Demonstrate how to perform a deeper analysis to find the specific sources of representativeness gaps.
- Show how to identify the top 5 over-represented and under-represented strata by inspecting the merged DataFrame of sample and benchmark proportions.
- Compare the GRI scores of two different surveys (e.g., load and analyze GD3 vs. GD4 data).

---

## Task 7: Finalize Repository

Complete the project by creating the final documentation and license files.

- **`LICENSE`**: Add the text for a permissive open-source license, such as the MIT License.
- **`gri/__init__.py`**: In `gri/__init__.py`, import the main functions from the `calculator` and `utils` modules to make them easily accessible to users of the package (e.g., `from .calculator import calculate_gri`).
- **Docstrings:** Review and ensure all functions, classes, and modules have clear, complete docstrings following a standard format (e.g., Google Style or NumPy style).
