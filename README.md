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

In addition to the GRI, which measures the proportional match, the **Diversity Score** measures the breadth of coverage of the sample. It is calculated as the percentage of relevant strata (with a population proportion $q_i$ above a certain threshold) that are actually represented in the sample.

## Data Sources

Calculating the GRI requires reliable benchmark data for the global population. The following sources are recommended for demographic data:

* **Age and Gender:**
    * United Nations, Department of Economic and Social Affairs, Population Division. (2023). *World Population Prospects 2022*.
* **Urban/Rural Distribution:**
    * United Nations, Department of Economic and Social Affairs, Population Division. (2018). *World Urbanization Prospects: The 2018 Revision*.
* **Religion:**
    * Pew Research Center. (2012). *The Global Religious Landscape*.

This repository provides tools to calculate the GRI and Diversity Score for any survey, given the survey data and the corresponding global population benchmarks.
