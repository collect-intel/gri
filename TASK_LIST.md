
1. Task: Diversity Score calculation clarification

**Status**: ✅ COMPLETED
**Priority**: High
**Dependencies**: None

1.A. Update the Diversity Score calculation in the README.md file to be more clear and precise given the following specification:

# Diversity Score (Coverage Rate)

Calculate the percentage of relevant strata (with a population proportion $q_i$ above a certain threshold $X$) that are actually represented in the sample (i.e. have at least one participant).

Let

* $X$ be a pre-defined threshold for the population $q_i$. Only consider strata $i$ where $q_i > X$ as "relevant" for this diversity score (to avoid penalizing for exceedingly small strata). We might by default choose $X = 1/(2N)$, where $N$ is the sample size, for an expected count of 0.5 (rounding up to 1 participant).

Using indicator functions, where $1(\text{condition})$ is 1 if the condition is true, and 0 otherwise:

$$\text{DiversityScore} = \frac{\text{NumRepresentedStrata}}{\text{NumRelevantStrata}} = \frac{\sum_{i \in I} 1(s_i > 0 \text{ AND } q_i > X)}{\sum_{i \in I} 1(q_i > X)}$$

1.B Update Diversity Score calculation scripts (and notebooks) to use ^ this formula.
1.C Update Notebooks to more clearly and prominently include the DiversityScore results alongside the GRI as part of the overall 'Scorecard' for a survey.
1.D Update or add tests for DiversityScore calculation.


2. Task: Refactor how Dimensions for the Benchmark and Survey data are defined to be more easily configurable.

**Status**: Pending  
**Priority**: High
**Dependencies**: Task 1 completed
**Implementation Strategy**: Modular config approach with separate files for dimensions, segments, and regions

Currently, much of the code for defining how the Dimensions are parsed and grouped from Benchmark/Survey raw data is hardcoded. This is not ideal and makes it difficult to easily add new Dimensions or change the way Dimensions are defined.

**Proposed Config Structure**:
- `config/dimensions.yaml`: Standard scorecard dimensions and available dimension combinations
- `config/segments.yaml`: Segment mappings (benchmark → standard naming, survey → standard naming)  
- `config/regions.yaml`: Geographic hierarchies (country → region → continent)

We want to change the Dimension definitions to be saved in a config file, and edit the scripts to take this config file or a dict as arguments (e.g. for using the scripts in a notebook).

For example,
dimensions: {
    # these are the current dimensions already calculated in the scripts now
    ```
    ['country', 'age_group', 'gender'],
    ['country', 'religion'],
    ['country', 'environment'],
    ```
    # additional courser-grained dimensions we should be able to dynamically calculate from the config file as well
    ```
    ['country'],
    ['religion'],
    ['enviornment'],
    ['age_group'],
    ['gender'],
    ['region', 'age_group', 'gender']
    ```
}

Granted, the benchmark data comes grouped by country - so I'm not sure if there's some logic that needs to be baked into how the segments get grouped together but the processor should handle this gracefully for any given valid dimensions. There should also be a clear way to delineate what segments ('country', 'age_group', 'gender', etc) are available.

I was trying to think of a way to similarlay have a config for mapping of Benchmark data columns to survey data columns, that could be the 'source' of the segment names used in the dimension config above. I imagine something like:
```
'age_group': {
    '18-25': ['15-19', '20-24'],  # Include 15-19 for approximate 18-25
    '26-35': ['25-29', '30-34'],
    '36-45': ['35-39', '40-44'],
    '46-55': ['45-49', '50-54'],
    '56-65': ['55-59', '60-64'],
    '65+': ['65-69', '70-74', '75-79', '80-84', '85-89', '90-94', '95-99', '100+']
},
'gender': {
    # this is an example of how we would explicitly "drop" the "other" or "Non-binary" gender results from the survey data because there isn't a corollary in the benchmark data. By not including a mapping for "Other" or "Non-binary", they would not get included in the 'gender' dimension.
    'Male': 'male',
    'Female': 'female'
},
'region': {
    'Africa': ['Algeria', 'Angola', 'Burundi', ... etc] # preferably there would be a structure that would allow instead for this to be an optional heierarchical taxonomy, so that 'Africa' could refer to ['North Africa', 'East Africa', 'West Africa', 'Subsaharan Africa']
    'North Africa': ['Egypt', ... etc]
    # for this grouping we may want to actually split this into more clear segment categories, so that we can clearly specify a distinction in dimensions between for example 'continent' vs 'region' 
},
'country': {
    # this could be a list of all of the 'official' country names that are used in the Survey to handle the mapping of different Becnhmark data country name versions to, something like this:
    'United States': ['United States of America','USA','US'],
    ... etc
},
'religion': {
    'Christianity': ['Catholic', 'Protestant', ... etc]
    'Islam': 'Islam',
    ... etc
}
```
But rather than just being a mapping of Benchmark -> GD Survey, to be really robust and extendable should probably be something like a mapping of Benchmark -> GRI Categories, and GD Survey -> GRI Categories, so that we could use this to calculate GRI for other kinds of survey data that aren't formatted exactly like GD is but using similar standard dimensions and segments to have comparable scores.

But I realize that this probably gets exceedingly complex for trying to map from the Raw benchmark data because of things like how the benchmark data for gender/age-group comes as two distinct files with age_group and gender already tied together (i.e. a 'male' ). I'd love for this to be somehow in a config file but I'm not sure the optimal way to structure this without making this overly complex. Perhaps we still have a basic script for processing the benchmark data to initially read in the data and do some data cleaning/filtering on the raw data, but then this script uses the config file in some sort of robust way to determine the appropriate way to group/name the benchmark data into segments and dimensions as defined by the config.

Think through some approaches to this and determine if there's a robust and streamlined way to implement a mapping config for Survey and Benchmark segments. If so, decide if this should go in the same config as the dimensions config or should be a separate file.


3. Task: Add a 'region' dimension that is a coarser-grained version of the 'country' dimension.
This should aggregate country data on the Benchmark side, but on the GD Survey side can map to explicit Regions already defined in the Survey data. If we have the config file descrbibed above this could help with this.

4. Task: Add some coarser dimensions to the standard scorecard throughout the scripts and Notebook. (By setting this in the dimension config file created above). Ensure support for these throughout the rest of the codebase and Documentation.

Speciically, in addition to the existing dimensions:
 ['country', 'age_group', 'gender'],
 ['country', 'religion'],
 ['country', 'environment']

 Add the following coarser dimensions:
    ['country'],
    ['region', 'age_group', 'gender'],
    ['region', 'religion'],
    ['region', 'enviornment'],
    ['region'],
    ['continent'],
    ['religion'],
    ['enviornment'],
    ['age_group'],
    ['gender'],

Note that because the benchmark data comes *grouped by country* (Country - Religion, Countr - Environment, Country - Age group - Gender), there will need to be a robust way to handle grouping this data into the coarser dimensions. For the single ['country'] dimension, unless we add a separate Raw benchmark data file that only lists population data by country, we should get this data from one of the existing benchmark data files, grouping/summing the other segments (i.e. use country - environment and add urban + rural). Whereas the reverse is true for example for ['religion'], which will need to group and add by religion.

5. Task: Get the scripts/notebooks working with the actual GD4 survey data rather than defaulting to the randomly generated sample data.

6. Task: Add a script to output the top "contributing" segments to the GRI.
That is, a script that ranks segments by |s_i - q_i| and also includes:
- how many percentage points of GRI (not the average scorecard, just for the dimension that segment was calculated in) they contribute; I belive this is just (([s_i - q_i]) / 2 ) * 100%
- the percentage points that they are "deviating" from the expectd value; this should just be (s_i - q_i) * 100%
- the % that the segment is "over-represented" or "under-represented" in the sample; this should just be ((s_i/q_i) - 1) * 100%

Include this in a notebook (the  3-advanced analysis) and use an example to demonstrate pointing out the top contributing N segments to the GRI that should be adjusted for in sampling.

7. Task: add a notebook comparing the GRI scores for all GD surveys to some other surveys for comparison (the World Values Survey)
If we have a mapping config of Survey segments -> GRI segments, this is a perfect example of how this gri tool can be extended to evaluate other surveys easily using a different configuration.
The raw files for the World Values Survey (slightly pre-processed to extract the relevant data) are available in data/raw/survey_data/wvs
These will need some careful processing/parsing as each WVS file is slightly distinct, and also don't include Country names, using ISO codes instead.
Consider updating the Raw data files to include Country names or otherwise slightly reformatting to make them easier to work with while not significantly altering so an observer can clearly map these Raw data files to the original WVS data files (i.e. keep the header names like V253	V240	V144G that refer to the original columns in the raw WVS download.)

8. Task: Add a script to calculate the 'Max possible GRI and Diveristy Scores' for the given dimensions.


### "Max Possible" Scores

The "max possible" score is the **expected theoretical best score** you could achieve for a given sample size (`N`). The term "expected" is used because the sampling model has a random component, meaning the score will vary slightly on each calculation. To find a stable "max" value, one must average the results of many simulations. With a finite number of samples, you can't perfectly match the true population proportions, but this model seeks the best possible outcome.


#### Max Possible GRI

To get the highest possible GRI, the **Total Variation Distance (TVD)** must be minimized. We do this by allocating the `N` samples using a hybrid formula:

* For strata large enough to receive at least one sample after rounding (`round(q_i * N) > 0`), the allocation is **deterministic**.
* For smaller strata, the allocation is **probabilistic** (`if rand() < q_i * N`), giving them a proportional chance of being included.

Because of this randomness, there is no single, deterministic Max GRI. The "max possible" score is found by running a Monte Carlo simulation (calculating the GRI many times) and averaging the results to find the stable **expected value**.

#### Max Possible Diversity Score

To maximize the Diversity Score, the sample of size `N` must be distributed to cover the **maximum number of unique strata**. The semi-stochastic sampling method is specifically designed to excel at this.

The calculation still depends on two factors:

1.  **Sample Size (N):** You can't represent more strata than your sample size.
2.  **Relevance Threshold (X):** A threshold (`q_i > X`) is used to define which strata are considered "relevant" in the denominator of the Diversity Score calculation.

The probabilistic part of the sampling model ensures that small-population strata aren't systematically ignored, leading to a much higher Diversity Score than a purely deterministic allocation would allow. The "Max Diversity Score" is also an **expected value** obtained through simulation.


## Instructions for Calculating Max GRI and Diversity Score

Here are the step-by-step instructions to create functions from scratch that can calculate the maximum possible **GRI (Global Representativeness Index)** and **Diversity Score** for a given sample size, `N`.

This method uses a "semi-stochastic sampling" approach to create an optimal sample allocation. This approach is a hybrid, using deterministic rounding for larger demographic groups and a probabilistic method for smaller ones. This ensures that smaller groups have a chance of being represented in the sample, which is crucial for a good diversity score.

---

### Function 1: `generate_optimal_sample`

This will be the core function that allocates the total sample of size `N` across all the demographic strata.

**Inputs:**
* A 2D array or dataframe of the **true population proportions**, let's call it `true_proportions`. Each cell `q_i` in this array represents the true population proportion for a specific demographic stratum `i`. The sum of all cells in `true_proportions` should be 1.0.
* An integer `N`, the **total sample size**.

**Logic (The "Semi-Stochastic Sampling" Method):**

1.  Initialize an empty 2D array with the same dimensions as `true_proportions`, called `sample_counts`. This will store the number of people sampled from each stratum.

2.  Iterate through each stratum `i` (each cell in `true_proportions`):
    * Get the true proportion `q_i` for that stratum.
    * Calculate the **ideal number of samples** for this stratum: `ideal_samples = q_i * N`.
    * Apply the following logic to determine the actual number of samples `n_i` for this stratum:
        * **If `round(ideal_samples) > 0`**:
            * Set `n_i = round(ideal_samples)`. This is the deterministic part.
        * **Else (if `round(ideal_samples)` is 0)**:
            * Generate a random number between 0 and 1.
            * **If `random_number < ideal_samples`**:
                * Set `n_i = 1`.
            * **Else**:
                * Set `n_i = 0`.
            * This is the stochastic part. It gives small strata a chance to be included.

3.  The `sample_counts` array now contains the number of sampled individuals from each stratum. However, the sum of all `n_i` in `sample_counts` will likely not be exactly `N` due to the rounding and the stochastic step. You need to adjust the sample counts to match `N`. A standard way to do this is with a correction step:
    * Calculate the current total sample size: `current_N = sum(all n_i)`.
    * Calculate the difference: `diff = N - current_N`.
    * If `diff` is positive, you need to add more samples. If negative, you need to remove them. You can distribute/remove this difference proportionally or by prioritizing strata that were most affected by rounding. For simplicity, you can randomly add/remove samples from strata that have `n_i > 0` until the total sum is `N`.

**Output:**
* A 2D array `final_sample_counts` of the same dimensions as `true_proportions`, where each cell contains the final allocated sample count `n_i`, and the sum of all cells is exactly `N`.

---

### Function 2: `calculate_max_gri`

This function will take the optimal sample and calculate the GRI score.

**Inputs:**
* The `true_proportions` array.
* The `final_sample_counts` array from the function above.
* The sample size `N`.

**Logic:**

1.  First, convert the `final_sample_counts` into a `sample_proportions` array by dividing each `n_i` by `N`. Let's call this `s_i`. So, `s_i = n_i / N`.

2.  Now, calculate the **Total Variation Distance (TVD)** using the formula:
    $$
    TVD = \frac{1}{2} \sum_{i} |s_i - q_i|
    $$
    (Sum the absolute differences between the sample proportion and true proportion for every stratum, then divide by 2).

3.  The **GRI** is then:
    $$
    GRI = 1 - TVD
    $$

**A Note on "Max" GRI:** Because of the `rand()` function in the sampling logic, each run will produce a slightly different GRI. To get a stable "maximum possible" GRI, you should run this process (both `generate_optimal_sample` and `calculate_max_gri`) many times (e.g., 1,000 or 10,000 times) and then report the **average GRI** from all these simulations. This will give you the *expected* max GRI.

---

### Function 3: `calculate_max_diversity_score`

This function will calculate the diversity score from the optimal sample.

**Inputs:**
* The `true_proportions` array.
* The `final_sample_counts` array.
* A **relevance threshold**, `X`. This is a small proportion (e.g., 0.0001, or you can set it to 0) used to define which strata are "relevant".

**Logic:**

1.  Count the **total number of relevant strata**. Iterate through the `true_proportions` array and count how many strata have a `q_i > X`.

2.  Count the **number of strata represented in the sample**. Iterate through the `final_sample_counts` array and count how many strata have `n_i > 0`.

3.  The **Diversity Score** is then the ratio:
    $$
    \text{Diversity Score} = \frac{\text{Number of represented strata}}{\text{Total number of relevant strata}}
    $$

Just like with GRI, you should run this through a Monte Carlo simulation (many runs) and report the **average Diversity Score** to get a stable estimate of the maximum possible score.




