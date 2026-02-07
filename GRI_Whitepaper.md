# The Global Representativeness Index: A Total Variation Distance Framework for Measuring Demographic Fidelity in Survey Research

**GRI Project Contributors**

*Correspondence: [correspondence email]*

---

## Abstract

Global survey research increasingly informs high-stakes decisions in AI governance, international development, and cross-cultural policy — yet no standardized metric exists to quantify how well a survey sample's demographic composition matches its target population. Response rates and demographic quotas, the prevailing proxies for sample quality, measure effort and coverage but not distributional fidelity. We introduce the Global Representativeness Index (GRI), a formal framework grounded in Total Variation Distance (TVD) that scores any survey sample against population benchmarks across multiple demographic dimensions simultaneously. The GRI produces interpretable scores on a [0, 1] scale, where 1 indicates a perfect demographic mirror of the target population and values below 0.4 signal serious distributional mismatch. We validate the framework through empirical application to six waves of the Global Dialogues survey on AI perceptions (N = 6,500 across 60+ countries), demonstrating that this purposive online survey achieves GRI scores of only 0.29–0.37 on fine-grained demographics — capturing roughly 39% of the theoretically maximum achievable representativeness at its sample size. We further introduce the Strategic Representativeness Index (SRI) for optimal sampling design, and show that the GRI connects to classical survey statistics through the design effect: low-GRI samples inflate estimation variance, reducing effective sample size in proportion to the squared coefficient of variation of the post-stratification weights. This connection provides the inferential justification for caring about distributional fidelity beyond its face-value interpretation. We release an open-source Python library implementing the complete framework. The GRI is applicable not only to survey research but also to auditing demographic composition of machine learning datasets and AI evaluation benchmarks. It provides researchers, funders, and policymakers with a rigorous, reproducible tool for evaluating, comparing, and improving the demographic quality of any dataset with categorical demographic attributes.

---

## 1. Introduction

### 1.1 The Stakes of Non-Representative Data

When the European Union drafted the AI Act [European Parliament, 2024], it drew on public opinion research to calibrate risk categories. When UNESCO published its Recommendation on the Ethics of Artificial Intelligence — the first global normative instrument on AI [UNESCO, 2021] — the consultation process claimed to represent "global perspectives." But whose perspectives? A survey that oversamples urban, English-speaking, highly-educated respondents from a handful of countries does not represent the world, regardless of how many countries appear in its sample frame. The gap between claimed and actual representativeness is not merely an academic concern. It shapes which voices inform regulation, which cultural values get encoded into AI systems, and which populations bear the costs of policies designed without their input.

This problem extends well beyond AI governance. The World Values Survey, Afrobarometer, Latinobarómetro, and other major cross-national instruments invest heavily in sampling design, yet each faces the fundamental challenge of measuring how closely their achieved samples match the populations they claim to represent. Response rates — once the gold standard of survey quality — have declined precipitously over recent decades and, in any case, measure participation rather than demographic fidelity [Brick and Williams, 2013]. Demographic quotas ensure minimum representation of specified groups but say nothing about whether the joint distribution of characteristics in the sample mirrors the population. Post-stratification weights can adjust for known imbalances, but they correct analysis rather than measuring the underlying problem.

What the field lacks is a formal, reproducible metric that answers a simple question: *How well does this sample's demographic composition match the target population?*

### 1.2 The Measurement Gap

The absence of a standardized representativeness metric creates three practical problems. First, researchers cannot objectively compare the demographic quality of different surveys or different waves of the same survey. Second, survey designers lack quantitative targets for sampling — they can set quotas for individual demographics but cannot optimize for the joint distribution across multiple dimensions. Third, consumers of survey research — policymakers, journalists, the public — have no way to assess claims of "global" or "representative" sampling beyond trusting the methodology section.

Existing approaches address pieces of this puzzle. R-indicators [Schouten, Cobben, and Bethlehem, 2009] measure the variation in response propensities across population subgroups, requiring auxiliary population data to model these propensities. R-indicators answer a related but distinct question: "How uniform is the response mechanism?" rather than "How closely does the achieved sample match the population distribution?" The GRI complements R-indicators by directly measuring the distributional outcome regardless of the mechanism that produced it — a distinction that matters particularly for non-probability samples where response propensities are undefined. Balance metrics from the causal inference literature [Rubin, 2001] assess covariate balance between treatment and control groups but are designed for experimental rather than survey contexts. Design effects and effective sample sizes quantify the efficiency loss from complex sampling designs but not the distributional distance between sample and population.

### 1.3 Contributions

This paper makes four contributions:

1. **A formal mathematical framework** for measuring survey representativeness based on Total Variation Distance, producing an interpretable score bounded on [0, 1] with clear properties and known behavior.

2. **A multi-dimensional approach** that evaluates representativeness across three benchmark dimensions simultaneously — Country × Gender × Age, Country × Religion, and Country × Urban/Rural Environment — using authoritative population data from the United Nations and Pew Research Center.

3. **Empirical validation** through application to six waves of the Global Dialogues survey (N ≈ 1,000 per wave), including Monte Carlo simulation of maximum achievable scores and efficiency analysis that separates sampling limitations from sampling failures.

4. **An open-source Python library** (`gri`) implementing the complete framework — core GRI calculation, a multi-dimensional scorecard, Monte Carlo simulation for maximum possible scores, the SRI metric variant, efficiency analysis, and publication-quality visualization — enabling any researcher to evaluate their survey's representativeness against global benchmarks.

### 1.4 Scope and Normative Commitments

A representativeness metric necessarily embeds normative choices. The GRI, as formulated with global population benchmarks, adopts a specific normative position: *one person, one unit of representativeness*. A survey is maximally representative when its demographic composition mirrors the world's population, weighting each person equally regardless of nationality, political influence, or institutional context.

This is a defensible default for research claiming to capture "global perspectives" — if you claim to represent the world, you should represent it in proportion to where people actually live and who they actually are. But it is not the only defensible choice. An AI governance survey might reasonably weight countries by their AI capability or regulatory influence; a climate adaptation survey might weight by climate vulnerability. The GRI framework accommodates such choices: researchers can substitute custom population benchmarks that reflect their specific representativeness goals. The global population benchmarks we provide are one instantiation of the framework, not its only use.

We also note an important distinction between what the GRI measures and what it does not. The GRI measures *marginal distributional distance* — how closely the sample's demographic composition matches the target population. It does not directly measure inferential quality: a sample with low GRI can produce unbiased estimates if appropriate post-stratification weights are applied, and a sample with high GRI can still produce biased estimates if respondents within each demographic cell are non-randomly selected (e.g., all highly educated). The GRI measures the *input* to inference — the demographic composition of the raw sample — not the quality of the estimates that emerge after weighting and adjustment. This complements design-based inference: good demographic composition reduces the reliance on post-stratification weights and the model assumptions they require.

---

## 2. Beyond Response Rates: The Case for Distributional Metrics

### 2.1 Classical Foundations and Their Limits

Survey sampling theory, formalized by Neyman [1934] and extended by Kish [1965] and Horvitz and Thompson [1952], provides rigorous frameworks for designing probability samples and producing unbiased estimators. In a well-designed probability sample, every member of the target population has a known, nonzero probability of selection, and design-based inference proceeds by weighting observations inversely to their selection probabilities. This machinery works beautifully when the sampling frame covers the target population, nonresponse is manageable, and the logistical infrastructure for probability sampling exists.

For global surveys, these conditions rarely hold simultaneously. No complete sampling frame exists for the world's population. Multi-country probability sampling requires coordinated fieldwork across dozens of national contexts with vastly different infrastructure, literacy levels, and cooperation norms. Even the most ambitious probability-based global surveys — the World Values Survey [Haerpfer et al., 2022], the Gallup World Poll [Gallup, 2024] — face coverage gaps, differential nonresponse, and practical constraints that introduce unknown deviations from the theoretical design.

Non-probability approaches — online panels, snowball sampling, convenience samples — are increasingly common in global research precisely because they are feasible at scale. The Global Dialogues survey on AI perceptions, which we use as our primary case study, employs purposive online sampling across 60+ countries. Such designs sacrifice the theoretical guarantees of probability sampling in exchange for breadth and speed. But the question of *how representative the resulting sample actually is* becomes correspondingly more urgent.

### 2.2 Representativeness Metrics in Current Practice

The most widely reported metric of survey quality — the response rate — has well-documented limitations as a proxy for representativeness. Groves [2006] demonstrated that response rates bear little systematic relationship to nonresponse bias, a finding subsequently reinforced by meta-analyses across survey contexts [Groves and Peytcheva, 2008]. A survey with a 60% response rate can be more biased than one with 20% if the nonresponse pattern in the former is more strongly correlated with the variables of interest.

R-indicators, introduced by Schouten, Cobben, and Bethlehem [2009], represent a significant advance. The R-indicator measures how much response propensities vary across population subgroups: a value of 1 indicates perfectly uniform response probabilities, while lower values signal differential nonresponse. Partial R-indicators decompose this variation by demographic characteristic. Like the GRI, R-indicators require auxiliary population data — specifically, data on the full target population that enables modeling of response propensities. The key conceptual difference is that R-indicators measure *mechanism* (variation in response propensities) while the GRI measures *outcome* (distance between achieved and target distributions). R-indicators are well-suited to probability surveys where response propensities are meaningful; the GRI applies equally to probability and non-probability samples, since it evaluates the demographic composition directly regardless of how it was generated.

Balance metrics from the propensity score literature — standardized mean differences, variance ratios, overlapping coefficients — assess whether distributions match across groups [Rubin, 2001; Stuart, 2010]. These are powerful for binary group comparisons (treated vs. control) but are not designed for evaluating a sample against a known population distribution across categorical demographic strata.

### 2.3 Total Variation Distance as a Foundation

Total Variation Distance (TVD) is the natural metric for comparing discrete probability distributions. For two distributions $P$ and $Q$ defined over the same finite set of outcomes, the TVD is:

$$\text{TVD}(P, Q) = \frac{1}{2} \sum_{i} |p_i - q_i|$$

TVD has several properties that make it ideal for measuring representativeness:

- **Bounded**: $0 \leq \text{TVD} \leq 1$, providing an interpretable scale.
- **Symmetric**: $\text{TVD}(P, Q) = \text{TVD}(Q, P)$, so it does not privilege sample or population.
- **Interpretable**: TVD equals the maximum difference in probability that $P$ and $Q$ assign to any event — equivalently, it equals the fraction of "probability mass" that must be moved to transform one distribution into the other.
- **Non-parametric**: It makes no distributional assumptions beyond finite discrete support.
- **Decomposable**: Each stratum's contribution $|p_i - q_i|$ to the total is identifiable, enabling segment-level diagnostics.

Alternative distance metrics exist. The Kullback-Leibler (KL) divergence is asymmetric, undefined when $q_i = 0$ (a common occurrence when a benchmark stratum has no sample members), and unbounded — making it ill-suited for a bounded representativeness score. The Hellinger distance, $H(P,Q) = \frac{1}{\sqrt{2}}\sqrt{\sum_i (\sqrt{p_i} - \sqrt{q_i})^2}$, is symmetric and bounded on [0, 1], but less directly interpretable than TVD: a Hellinger distance of 0.3 has no simple prose description, while a TVD of 0.3 means "30% of the sample's demographic weight is misallocated." The chi-squared distance is sensitive to small expected counts — precisely the scenario that arises frequently in global demographic benchmarks where many countries constitute less than 0.1% of the world population.

One might ask whether a Hellinger-based index would eliminate the need for a separate Diversity Score, since Hellinger distance penalizes missing rare strata more aggressively through its square-root transformation. We considered this and opted for the TVD + Diversity Score decomposition for three reasons. First, **interpretability**: TVD has a direct prose interpretation ("fraction of probability mass misallocated") that Hellinger lacks — a Hellinger distance of 0.3 requires technical knowledge to interpret. For a metric intended for use by survey practitioners, policymakers, and funders, interpretability is a primary design requirement. Second, **decomposability**: TVD decomposes additively into per-stratum contributions ($|p_i - q_i|/2$), enabling the segment-level diagnostics that make the GRI actionable. Hellinger decomposes into $(\sqrt{p_i} - \sqrt{q_i})^2$ terms, which are less intuitive as individual segment diagnostics. Third, **separation of concerns**: distributional fidelity (how closely proportions match) and coverage (how many strata are reached) are conceptually distinct aspects of representativeness that practitioners need to evaluate independently. A Hellinger-based index would merge them into a single number, losing this diagnostic value. The TVD + Diversity Score combination provides two clearly interpretable numbers rather than one opaque one.

We note that TVD and Hellinger distance are formally related: $H^2(P,Q) \leq \text{TVD}(P,Q) \leq H(P,Q)\sqrt{2}$ (see Appendix A.3), so the two metrics are never wildly discrepant. Our choice is primarily one of transparency and usability, not mathematical necessity.

---

## 3. Methodology

### 3.1 The Global Representativeness Index

#### 3.1.1 Formal Definition

Let $\mathcal{S} = \{s_1, s_2, \ldots, s_K\}$ denote the set of $K$ demographic strata defined by the cross-classification of relevant demographic variables. For a survey sample of size $N$ and a reference population, define:

- $p_i$: the proportion of the survey sample in stratum $i$, where $\sum_{i=1}^K p_i = 1$
- $q_i$: the proportion of the reference population in stratum $i$, where $\sum_{i=1}^K q_i = 1$

The **Global Representativeness Index** is:

$$\text{GRI} = 1 - \frac{1}{2} \sum_{i=1}^{K} |p_i - q_i|$$

Equivalently, $\text{GRI} = 1 - \text{TVD}(P, Q)$.

#### 3.1.2 Properties

**Boundedness.** Since $\text{TVD} \in [0, 1]$, we have $\text{GRI} \in [0, 1]$. A score of 1 indicates perfect distributional match ($p_i = q_i$ for all $i$); a score of 0 indicates complete mismatch (the sample and population occupy disjoint strata).

**Proof of bounds.** The lower bound TVD = 0 is achieved when $P = Q$. The upper bound TVD = 1 is achieved when $P$ and $Q$ have disjoint support — i.e., $p_i > 0 \implies q_i = 0$ and vice versa. Since $\sum_i |p_i - q_i| \leq \sum_i p_i + \sum_i q_i = 2$ when supports are disjoint, we get TVD $= \frac{1}{2} \cdot 2 = 1$. □

**Monotonicity.** Improving the match between $p_i$ and $q_i$ for any stratum (moving probability mass toward the population distribution) cannot decrease the GRI.

**Decomposability.** Each stratum $i$ contributes $\frac{1}{2}|p_i - q_i|$ to the total representativeness deficit. This enables identification of specific demographic segments driving misrepresentation.

**Invariance to stratum ordering.** The GRI depends only on the set of proportions, not their labeling — it is a property of the distributions, not of any particular enumeration.

#### 3.1.3 Interpretation Scale

We propose the following interpretation guidelines, derived from the TVD interpretation (fraction of misallocated probability mass) and calibrated against Monte Carlo simulations of achievable scores at various sample sizes. The thresholds correspond to natural breakpoints: at GRI = 0.8, less than 20% of the sample's demographic mass needs to be moved to match the population — a level achievable at moderate sample sizes for low-dimensional strata; at GRI = 0.4, more than 60% of the mass is misallocated, a level at which substantive demographic bias is likely to affect aggregate survey estimates:

| GRI Score | Interpretation | Meaning |
|-----------|---------------|---------|
| 0.8 – 1.0 | Excellent | Less than 20% of demographic weight misallocated |
| 0.6 – 0.8 | Good | 20–40% misallocation; usable for most purposes |
| 0.4 – 0.6 | Moderate | 40–60% misallocation; interpret with caution |
| 0.0 – 0.4 | Poor | Over 60% misallocation; substantive bias likely |

These thresholds are inherently context-dependent. A GRI of 0.5 may be excellent for a dimension with 2,699 strata (Country × Gender × Age) but poor for one with 6 strata (Continent). The maximum achievable GRI at a given sample size provides a more meaningful benchmark, as we discuss in Section 3.4.

### 3.2 The Diversity Score

The GRI measures distributional fidelity — how closely the sample's demographic *proportions* match the population. A complementary question is coverage: *How many of the population's demographic strata does the sample reach at all?*

A sample could, in principle, concentrate all its observations in a single stratum that happens to be small in the population, achieving low GRI but "covering" that stratum perfectly. Conversely, a sample that spreads across many strata with roughly equal allocation might have moderate GRI but excellent coverage. The Diversity Score captures this second dimension.

#### 3.2.1 Definition

Let $N$ be the sample size and define the relevance threshold $X = 1/N$. A population stratum is **relevant** if its population proportion exceeds $X$ — i.e., if we would expect at least one observation from that stratum in a perfectly proportional sample of size $N$. A relevant stratum is **represented** if at least one sample member belongs to it. The Diversity Score is:

$$\text{DiversityScore} = \frac{|\{i : p_i > 0 \text{ and } q_i > X\}|}{|\{i : q_i > X\}|}$$

The threshold $X = 1/N$ is derived from sampling theory. Under simple random sampling from a population where stratum $i$ has proportion $q_i$, the expected count in stratum $i$ is $Nq_i$. For $q_i > 1/N$, this expectation exceeds 1, giving a probability of at least $1 - e^{-1} \approx 0.632$ of observing at least one member (via the Poisson approximation). The threshold thus identifies strata where non-representation signals a systematic sampling gap rather than random chance.

Alternative thresholds — $1/(2N)$ (approximately 39% observation probability) and $2/N$ (approximately 86% probability) — were evaluated empirically. The $1/(2N)$ threshold overestimates achievable diversity by 30–60% in Monte Carlo simulations, as many strata near the threshold appear in fewer than half of simulated optimal samples. The $1/N$ threshold better aligns theoretical expectations with observed coverage rates.

### 3.3 Multi-Dimensional Scorecard

A single aggregate score obscures important structure. A survey might achieve high representativeness on gender but poor representativeness on the joint distribution of country, gender, and age. The GRI framework therefore computes scores across multiple dimensions simultaneously, producing a **representativeness scorecard**.

#### 3.3.1 Primary Dimensions

Three primary dimensions define the cross-classified strata at the finest grain. The choice of these dimensions reflects three criteria: (1) availability of authoritative, country-level population data covering virtually all nations; (2) established relevance to opinion formation and social behavior in the social science literature; and (3) observability in survey contexts (respondents can reliably self-report all three). We acknowledge that other dimensions — education level, income, language, disability status, ethnicity — are arguably as important for some research questions. We omit them not because they are less important but because no single authoritative data source provides globally comparable, country-level distributions for these variables. The framework is explicitly extensible: any categorical variable with a population benchmark can be added as a new scorecard dimension.

1. **Country × Gender × Age** (2,699 strata): The most demanding dimension, requiring correct proportions across the joint distribution of 195+ countries, 2 genders, and 6 age brackets (18–24, 25–34, 35–44, 45–54, 55–64, 65+). Benchmark: UN World Population Prospects 2023.

2. **Country × Religion** (1,607 strata): Proportions across 195+ countries and 8 religious categories (Christian, Muslim, Hindu, Buddhist, Jewish, Sikh, Unaffiliated, Other). Benchmark: Pew Research Center Global Religious Landscape 2010.

3. **Country × Environment** (449 strata): Proportions across 195+ countries and urban/rural/suburban categories. Benchmark: UN World Urbanization Prospects 2018.

#### 3.3.2 Auxiliary Dimensions

The scorecard also evaluates representativeness at coarser geographic resolutions — Region (22 UN sub-regions) and Continent (6 continents) — crossed with the same demographic variables, plus marginal distributions of each demographic variable alone. This produces a hierarchy of 13 dimensions ranging from the most demanding (Country × Gender × Age) to the least (Gender alone), enabling researchers to identify at which level of geographic granularity their sample's representativeness breaks down.

#### 3.3.3 Benchmark Data Sources

| Source | Variables | Coverage | Year | Strata |
|--------|-----------|----------|------|--------|
| UN World Population Prospects | Country, Gender, Age | 237 countries/areas | 2023 | 2,699 |
| Pew Global Religious Landscape | Country, Religion | 232 countries | 2010 | 1,607 |
| UN World Urbanization Prospects | Country, Urban/Rural | 233 countries | 2018 | 449 |

The temporal mismatch among benchmarks — particularly the 2010 religious composition data — is a limitation we address in Section 7. Pew's Global Religious Landscape remains the most comprehensive cross-national religious demography dataset available; updates from the Pew 2015 and subsequent estimates could be incorporated as they become available in disaggregated form.

### 3.4 Maximum Possible Scores and Efficiency Ratios

A critical insight for interpreting GRI scores is that perfect representativeness (GRI = 1.0) is mathematically impossible at realistic sample sizes when the number of strata is large. With 2,699 Country × Gender × Age strata and a sample of 1,000, many strata have population proportions below $1/N = 0.001$, meaning perfect proportional representation would require fractional people.

We estimate the **maximum achievable GRI** through Monte Carlo simulation. For each dimension and sample size:

1. Draw an optimal sample allocation $\mathbf{n}^*$ by computing $n_i^* = \text{round}(q_i \cdot N)$ for each stratum and randomly assigning the residual.
2. Repeat 1,000 times with different random seeds for the residual allocation.
3. Report the mean maximum GRI across simulations.

Results for a sample of $N = 1{,}000$:

| Dimension | Max GRI (mean) | Max Diversity (mean) | Total Strata | Relevant Strata |
|-----------|---------------|---------------------|--------------|-----------------|
| Country × Gender × Age | 0.792 | 0.925 | 2,699 | 376 |
| Country × Religion | 0.938 | 0.970 | 1,607 | 182 |
| Country × Environment | 0.950 | 0.977 | 449 | 192 |

At $N = 1{,}000$, even a perfectly allocated sample can achieve at most 0.792 on Country × Gender × Age. This theoretical ceiling contextualizes empirical scores: a GRI of 0.30 against a maximum of 0.79 represents an **efficiency ratio** of 0.38, meaning the sample captures 38% of the representativeness that is theoretically achievable at that sample size.

The efficiency ratio is defined as:

$$\text{Efficiency} = \frac{\text{GRI}_{\text{actual}}}{\text{GRI}_{\text{max}}}$$

This metric separates two sources of low GRI scores: *structural limitations* (too few respondents to fill all strata) versus *allocation failures* (respondents concentrated in the wrong strata). The former is addressed by increasing sample size; the latter by improving sampling strategy.

An important caveat: the Monte Carlo maximum assumes an oracle allocator who can place respondents in any stratum at will. Real surveys face additional constraints — recruitment friction, language barriers, internet access, and differential willingness to participate — that make even the integer-constrained optimum unachievable in practice. The max GRI should therefore be interpreted as an *upper bound on the upper bound*: the true achievable maximum for any real survey is lower, by an amount that depends on the sampling modality and context. Nevertheless, the efficiency ratio remains useful as a benchmark — low efficiency against even this generous ceiling indicates clear room for improvement in sampling strategy.

Monte Carlo simulations across sample sizes reveal the scaling behavior:

| Sample Size | Max GRI (Country × Gender × Age) | Max GRI (Country × Religion) | Max GRI (Country × Environment) |
|-------------|----------------------------------|-----------------------------|---------------------------------|
| 100 | 0.430 | 0.721 | 0.714 |
| 250 | 0.581 | 0.839 | 0.844 |
| 500 | 0.691 | 0.898 | 0.906 |
| 1,000 | 0.792 | 0.938 | 0.950 |
| 2,000 | 0.873 | 0.965 | 0.976 |

### 3.5 The Strategic Representativeness Index (SRI)

The core GRI treats all deviations from population proportions equally. An alternative weighting scheme is useful for survey design.

#### 3.5.1 Definition and Motivation

Proportional allocation — the target implicit in the GRI — allocates sample in proportion to population size. But proportional allocation is not statistically optimal for minimizing estimation error across all strata. Neyman allocation [Neyman, 1934] allocates more sample to strata with higher variance, which for small strata means substantially more than their population share.

The **Strategic Representativeness Index** replaces the population-proportional target with a square-root-proportional target:

$$s_i^* = \frac{\sqrt{q_i}}{\sum_j \sqrt{q_j}}$$

$$\text{SRI} = 1 - \frac{1}{2} \sum_{i=1}^K |p_i - s_i^*|$$

The square-root transformation has a formal connection to optimal allocation theory. Under Neyman allocation [Neyman, 1934], the optimal sample allocation for minimizing total estimation error is proportional to $q_i \sigma_i$, where $\sigma_i$ is the within-stratum standard deviation. When within-stratum variances are unknown and assumed equal (a common default), the optimal allocation simplifies to proportional allocation. The square-root target represents an intermediate case: it can be derived as the allocation that minimizes the maximum relative estimation error across strata when within-stratum variances are proportional to stratum size — a reasonable assumption when larger strata exhibit more heterogeneity. More practically, $\sqrt{q_i}$ moderately boosts the target allocation for smaller strata while tempering it for larger ones. A stratum constituting 0.1% of the population receives a strategic target roughly 3.2× its population share; a stratum at 10% receives approximately the same. This rebalancing reflects the diminishing marginal information gain from oversampling large populations and the high marginal value of including underrepresented groups.

The SRI is particularly useful for **prospective survey design**: it defines a sampling target that optimizes statistical power across the full demographic distribution rather than merely mirroring population proportions.

### 3.6 The Inferential Cost of Low Representativeness

A natural objection to the GRI is: "If the sample's demographic composition doesn't match the population, can't we simply apply post-stratification weights to correct the estimates?" The answer is yes — but at a quantifiable cost to statistical precision. This section establishes the formal connection between distributional mismatch (as measured by the GRI) and inferential quality (as measured by classical survey statistics).

#### 3.6.1 Post-Stratification Weights and Variance Inflation

When a survey sample has demographic proportions $p_i$ that differ from population proportions $q_i$, the standard correction is to apply post-stratification weights $w_i = q_i / p_i$ to each respondent in stratum $i$. Under these weights, the weighted mean is an unbiased estimator of the population mean — for any outcome variable — regardless of how distorted the sample demographics are (assuming all strata are represented and responses within strata are unbiased).

But reweighting does not come for free. The variance of the weighted estimator is inflated relative to what would be achieved by a simple random sample of the same size. The **design effect** quantifies this inflation:

$$d_{\text{eff}} = 1 + \text{CV}^2(w)$$

where $\text{CV}^2(w) = \text{Var}(w) / \bar{w}^2$ is the squared coefficient of variation of the weights. This is the Kish [1965] approximation for unequal weighting effects.

The design effect has a direct interpretation: a design effect of 3.0 means the weighted estimates have the same precision as a simple random sample one-third the size. The **effective sample size** makes this concrete:

$$N_{\text{eff}} = \frac{N}{d_{\text{eff}}}$$

A survey with 1,000 respondents and a design effect of 3.0 has an effective sample size of only 333 — two-thirds of the data collection budget has been consumed by the need to reweight.

#### 3.6.2 Connection to Distributional Mismatch

The connection between the GRI and the design effect is through the weight distribution. When sample proportions $p_i$ closely match population proportions $q_i$, the weights $w_i = q_i / p_i$ are all near 1.0, the coefficient of variation of weights is small, and the design effect approaches 1.0 (no precision loss). As sample proportions diverge from population proportions, some weights become very large (underrepresented strata) and others very small (overrepresented strata), the CV of weights increases, and precision degrades.

Formally, the design effect is driven by the chi-squared divergence between sample and population distributions:

$$d_{\text{eff}} = 1 + \text{CV}^2(w) = \sum_i \frac{q_i^2}{p_i}$$

While the GRI is based on TVD (the $L_1$ distance between distributions), the design effect is driven by a ratio-based divergence (related to the $\chi^2$ distance). These two measures are related but not identical: TVD treats a 5-percentage-point deviation equally regardless of the base rate, while the design effect penalizes deviations in small strata much more severely (because $q_i / p_i$ diverges when $p_i$ is small relative to $q_i$).

This distinction is precisely why we recommend reporting *both* the GRI and the design effect rather than replacing one with the other. The GRI measures what it should measure — the overall distributional distance, with equal treatment of all probability mass — and the design effect captures the inferential consequence, which is disproportionately driven by strata where the sample is thin relative to the population.

#### 3.6.3 Why Not "Just Reweight"?

The design effect framework reveals four reasons why post-stratification reweighting is not a substitute for representative sampling:

1. **Variance inflation is quadratic, not linear.** Doubling the ratio $q_i / p_i$ in a stratum quadruples that stratum's contribution to the design effect. Severe distributional mismatch destroys precision.

2. **Empty strata are uncorrectable.** If $p_i = 0$ for some stratum (no respondents), the weight $q_i / p_i$ is undefined. No amount of reweighting can impute a missing voice. The Diversity Score captures this complementary failure mode.

3. **Extreme weights increase model dependence.** When some weights are very large, the weighted estimates become sensitive to the specific responses of a handful of highly-weighted individuals, increasing the influence of outliers and model assumptions.

4. **Reweighting treats the symptom, not the cause.** A low-GRI sample that is reweighted produces unbiased point estimates but with wide confidence intervals. Improving the GRI through better sampling reduces both bias *and* variance simultaneously — a strictly superior outcome.

#### 3.6.4 The Complete Reporting Framework

Based on this analysis, we recommend that surveys report six complementary metrics, each capturing a distinct aspect of sample quality:

| Metric | What It Measures | Primary Audience |
|--------|-----------------|-----------------|
| **GRI** | Distributional fidelity (TVD from target) | Researchers, reviewers |
| **Max GRI** | Structural ceiling at given N | Survey designers |
| **Efficiency Ratio** | GRI / Max GRI — allocation quality | Survey designers |
| **Design Effect** | Variance inflation from reweighting | Statisticians, analysts |
| **Effective N** | N / d_eff — precision budget | All stakeholders |
| **Diversity Score** | Strata coverage fraction | Researchers, funders |

The GRI and Diversity Score describe the *state* of the sample. The Max GRI and Efficiency Ratio contextualize that state against structural constraints. The Design Effect and Effective N translate the state into *inferential consequences*. Together, these six numbers provide a complete picture of sample quality that no single metric can capture.

---

## 4. Empirical Application: The Global Dialogues Case Study

### 4.1 The Global Dialogues Survey

The Global Dialogues (GD) is an ongoing longitudinal survey of public perceptions of artificial intelligence, designed to capture diverse global perspectives on AI development and governance. Six waves (GD1–GD6) have been completed, each recruiting approximately 1,000 participants through online purposive sampling across 50–70 countries. Participants self-report demographic characteristics including country of residence, gender, age group, religion, and urban/rural environment.

The GD provides an ideal case study for the GRI framework for three reasons. First, it explicitly aims for global representativeness without employing probability sampling — exactly the scenario where a formal representativeness metric is most needed. Second, its longitudinal design enables tracking representativeness trends across waves. Third, its moderate sample size (N ≈ 1,000 per wave) represents a common scale for global opinion research, where the tension between feasibility and representativeness is acute.

| Wave | N | Countries | Period |
|------|---|-----------|--------|
| GD1 | 1,280 | ~60 | Wave 1 |
| GD2 | 1,105 | ~55 | Wave 2 |
| GD3 | 971 | 63 | Wave 3 |
| GD4 | 1,050 | 57 | Wave 4 |
| GD5 | 1,057 | ~60 | Wave 5 |
| GD6 | 1,037 | ~60 | Wave 6 |

### 4.2 GRI Scores Across Six Waves

Table 1 presents the core GRI scores for the three primary cross-classified dimensions plus selected auxiliary dimensions.

**Table 1: GRI Scores Across Global Dialogues Waves GD1–GD6**

| Dimension | GD1 | GD2 | GD3 | GD4 | GD5 | GD6 | Mean | SD |
|-----------|-----|-----|-----|-----|-----|-----|------|-----|
| Country × Gender × Age | 0.293 | 0.282 | 0.374 | 0.319 | 0.301 | 0.292 | 0.310 | 0.033 |
| Country × Religion | 0.471 | 0.474 | 0.515 | 0.518 | 0.484 | 0.481 | 0.490 | 0.021 |
| Country × Environment | 0.369 | 0.339 | 0.387 | 0.390 | 0.354 | 0.345 | 0.364 | 0.021 |
| Country | 0.516 | 0.502 | 0.539 | 0.571 | 0.527 | 0.519 | 0.529 | 0.024 |
| Region | 0.745 | 0.739 | 0.791 | 0.799 | 0.738 | 0.734 | 0.758 | 0.029 |
| Continent | 0.832 | 0.830 | 0.886 | 0.883 | 0.773 | 0.802 | 0.834 | 0.043 |
| Religion | 0.817 | 0.819 | 0.833 | 0.826 | 0.813 | 0.806 | 0.819 | 0.009 |
| Gender | 0.989 | 0.990 | 0.996 | 0.979 | 0.986 | 0.995 | 0.989 | 0.006 |

Several patterns emerge. **Gender balance is essentially perfect** across all waves (GRI > 0.97), reflecting that gender parity is relatively straightforward to achieve in online convenience sampling. **Religious representativeness at the global level is good** (GRI ≈ 0.82), because the major religious categories are broad enough that most samples naturally cover them. **Continental representativeness is also good** (GRI ≈ 0.83), as the GD recruits from all inhabited continents.

The representativeness picture deteriorates sharply as granularity increases. **Country-level GRI averages 0.53**, meaning nearly half the sample's demographic weight is allocated to the wrong countries. The most demanding dimension — **Country × Gender × Age — averages only 0.31**, indicating that roughly 69% of the sample's joint country-gender-age demographic weight is misallocated relative to the global population.

### 4.3 Efficiency Analysis

Raw GRI scores must be interpreted against what is theoretically achievable. Table 2 shows the efficiency ratios — actual GRI divided by maximum achievable GRI — for the primary dimensions.

**Table 2: Efficiency Ratios (Actual GRI / Max GRI) for Primary Dimensions**

| Dimension | Max GRI (N≈1000) | GD1 | GD2 | GD3 | GD4 | GD5 | GD6 | Mean Efficiency |
|-----------|-------------------|-----|-----|-----|-----|-----|-----|-----------------|
| Country × Gender × Age | 0.792 | 37.0% | 35.6% | 47.3% | 40.3% | 38.0% | 36.9% | 39.2% |
| Country × Religion | 0.938 | 50.2% | 50.6% | 54.9% | 55.2% | 51.6% | 51.3% | 52.3% |
| Country × Environment | 0.950 | 38.8% | 35.7% | 40.7% | 41.0% | 37.2% | 36.3% | 38.3% |

The efficiency ratios paint a more nuanced picture than raw scores alone. For Country × Religion, the GD achieves about 52% of the theoretical maximum — meaning about half the remaining representativeness gap is due to the structural impossibility of perfectly allocating ~1,000 people across 1,607 strata, and the other half is due to actual sampling imbalances. For Country × Gender × Age, efficiency is lower at ~39%, suggesting more room for improvement through better sampling design.

GD3 stands out with notably higher efficiency (47.3% for Country × Gender × Age) compared to other waves, suggesting that its particular geographic and demographic recruitment pattern happened to align better with global population proportions.

### 4.4 Diversity Scores and Strata Coverage

**Table 3: Diversity Scores (Strata Coverage) Across Waves**

| Dimension | GD1 | GD2 | GD3 | GD4 | GD5 | GD6 | Mean |
|-----------|-----|-----|-----|-----|-----|-----|------|
| Country × Gender × Age | 0.464 | 0.458 | 0.470 | 0.476 | 0.464 | 0.458 | 0.465 |
| Country × Religion | 0.538 | 0.521 | 0.453 | 0.487 | 0.496 | 0.521 | 0.503 |
| Country × Environment | 0.434 | 0.414 | 0.394 | 0.393 | 0.372 | 0.372 | 0.397 |
| Continent | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Gender | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

The Diversity Scores reveal that the GD consistently covers only about 46% of relevant Country × Gender × Age strata — meaning more than half of the demographic segments where we would expect at least one participant (given the sample size) go entirely unrepresented. At coarser levels, coverage is complete: all continents and both binary genders are always represented.

### 4.5 Detailed Analysis: GD4

The GD4 wave (N = 1,050, 57 countries) illustrates the diagnostic power of segment-level GRI decomposition. The five largest contributors to the Country × Religion representativeness gap were:

- **Kenya × Christianity**: 17.3% of sample vs. 0.5% of global population (+16.8% deviation)
- **China × Unaffiliated**: 2.3% of sample vs. 10.2% of global population (-7.8% deviation)
- **India × Urban**: 14.7% of sample vs. 6.0% of global population (+8.6% deviation)
- **India × Rural**: 1.3% of sample vs. 11.7% of global population (-10.4% deviation)
- **China × Urban**: 2.8% of sample vs. 11.0% of global population (-8.1% deviation)

This decomposition identifies two structural patterns in the GD sampling. First, **geographic concentration**: Kenya (18.7% of sample) and India (16.0%) together constitute 34.7% of the sample despite representing roughly 8% of the global population. This concentration inflates their demographic segments at the expense of more populous countries — particularly China, which constitutes 18% of the world's population but receives far less than proportional representation.

Second, **urban bias**: urban segments are systematically overrepresented across countries, while rural segments are underrepresented. India's urban population constitutes 6% of the world but 14.7% of the GD4 sample, while India's rural population — 11.7% of the world — constitutes only 1.3% of the sample. This 23:1 urban-to-rural oversampling ratio reflects the inherent bias of online surveys toward connected, urban populations.

### 4.6 Metric Comparison: GRI, SRI, and Efficiency Ratio

**Table 4: Comparison of GRI and SRI for GD5 (N = 1,057)**

| Dimension | GRI | SRI | Max GRI | Efficiency |
|-----------|-----|-----|---------|-----------|
| Country × Gender × Age | 0.301 | 0.306 | 0.792 | 38.0% |
| Country × Religion | 0.484 | 0.424 | 0.938 | 51.6% |
| Country × Environment | 0.354 | 0.336 | 0.950 | 37.3% |
| Country | 0.527 | 0.457 | — | — |
| Region | 0.738 | 0.749 | — | — |
| Continent | 0.773 | 0.841 | — | — |
| Religion | 0.813 | 0.745 | — | — |
| Gender | 0.986 | 0.986 | — | — |

The two metrics tell coherent but distinct stories. **GRI** provides the strictest assessment: the GD5 sample achieves only 0.301 on Country × Gender × Age, meaning the sample is far from a proportional mirror of the world.

**SRI** scores are generally similar to GRI but differ at extremes. For Continent, SRI is higher (0.841 vs. 0.773), because the square-root transformation increases the target allocation for smaller continents (Oceania, South America), which the GD happens to cover relatively well. For Religion, SRI is lower (0.745 vs. 0.813), because the strategic target boosts smaller religions (Judaism, Sikhism) that the sample underrepresents.

The **efficiency ratio** contextualizes raw GRI scores against structural constraints. Country × Religion has the highest efficiency (51.6%), indicating that about half the gap between the GD5 score and perfect representativeness is due to the structural impossibility of perfectly allocating ~1,000 people across 1,607 strata, while the other half reflects actual sampling imbalances. Country × Gender × Age and Country × Environment have lower efficiencies (~38%), suggesting more room for improvement through better sampling strategy on those dimensions.

### 4.7 Cross-Wave Trends

Across six waves, Country × Gender × Age GRI is remarkably stable, ranging from 0.282 (GD2) to 0.374 (GD3) with no clear trend of improvement. This stability suggests that the GD's sampling method — online purposive recruitment — reaches a natural ceiling of demographic representativeness that is not easily surpassed without deliberate stratified oversampling of underrepresented segments.

GD3 is the consistent outlier, achieving the highest GRI on most dimensions despite having the smallest sample (N = 971). This wave's superior scores likely reflect a particularly well-distributed geographic recruitment pattern rather than a larger sample. The Country-level GRI for GD3 (0.539) and its continental GRI (0.886) — the highest in the series — corroborate this interpretation.

---

## 5. What Counts as Representative?

### 5.1 The Interpretation Challenge

A GRI of 0.31 for Country × Gender × Age sounds alarming — nearly 70% of the demographic weight is misallocated. But three considerations moderate this alarm.

First, **high GRI on fine-grained dimensions is mathematically constrained at moderate sample sizes.** The maximum achievable GRI for Country × Gender × Age at N = 1,000 is 0.792 — meaning even a sample drawn by an omniscient designer with perfect proportional allocation would fail to reach the "excellent" threshold of 0.8. At N = 2,000, the maximum rises to 0.873. Achieving truly excellent representativeness on fine-grained dimensions requires sample sizes in the thousands. (We note that the GD's scores reflect purposive online sampling; probability-based global surveys like the World Values Survey may achieve different GRI profiles, and applying the framework to such surveys is an important direction for future validation.)

Second, **the GRI measures a different property than most surveys are designed to optimize.** Many surveys target specific analytic comparisons (e.g., between countries, between age groups) rather than perfect demographic mirroring. A survey designed to compare AI attitudes between the US and China might intentionally oversample both, achieving its analytic goals perfectly while scoring poorly on a global GRI. The GRI measures distributional fidelity, not fitness for purpose.

Third, **the gap between actual and maximum GRI is more informative than the raw score.** An efficiency ratio of 39% tells the practitioner: "Your sampling strategy captures less than 40% of the representativeness that is theoretically possible at your sample size." This directly suggests room for improvement — and the segment-level decomposition identifies *where*.

### 5.2 Why Religion Scores Higher Than Demographics

Across all waves, Country × Religion GRI (mean: 0.49) substantially exceeds Country × Gender × Age (mean: 0.31). Three factors explain this pattern.

First, **fewer strata**: Country × Religion has 1,607 strata vs. 2,699, making proportional allocation less demanding. Second, **larger stratum proportions**: the major religious groups (Christianity, Islam, Hinduism, Unaffiliated) collectively account for over 85% of the global population, so even imperfect sampling tends to capture them. Third, **geographic correlation**: religious composition is strongly correlated with geography, so a sample that covers many countries naturally captures religious diversity, even without religious stratification.

The Country × Environment dimension (mean GRI: 0.36), despite having the fewest strata (449), scores lower than Country × Religion. This reflects the systematic urban bias of online surveys. Urban populations have internet access; rural populations — who constitute roughly 44% of the world — are structurally harder to reach through online recruitment. This is a sampling modality limitation, not a sampling strategy failure.

### 5.3 The Efficiency Ratio as Diagnostic

The efficiency ratio separates two fundamentally different problems:

- **Low efficiency with low max GRI** (e.g., Country × Gender × Age at N = 100, max GRI = 0.43): The sample is too small for this level of granularity. The solution is either a larger sample or coarser strata.
- **Low efficiency with high max GRI** (e.g., Country × Religion at N = 1,000, max GRI = 0.94, actual GRI ≈ 0.49, efficiency ≈ 52%): The sample is large enough but poorly allocated. The solution is better sampling strategy.
- **High efficiency with low raw GRI**: The sample is doing the best it can at its size. Further improvement requires more respondents, not different respondents.

For the Global Dialogues, the efficiency analysis reveals that Country × Religion has the most room for strategic improvement: the theoretical maximum at N = 1,000 is 0.94, but achieved scores hover around 0.49 — an efficiency of only 52%. Targeted oversampling of countries with large non-Christian, non-Muslim populations (China, India, Japan) would substantially close this gap.

### 5.4 Beyond Surveys: Applications to Machine Learning Dataset Auditing

The GRI framework applies directly to any dataset with categorical demographic attributes and a reference population distribution — a criterion met by many machine learning (ML) training datasets and evaluation benchmarks. The demographic composition of ML datasets directly affects model behavior: training data skewed toward particular demographics produces models that perform better on those groups and worse on others [Buolamwini and Gebru, 2018]. Evaluation benchmarks with demographic imbalances may overstate model performance for well-represented groups.

Current practices for documenting dataset demographics — Datasheets for Datasets [Gebru et al., 2021], Model Cards [Mitchell et al., 2019], and Data Statements [Bender and Friedman, 2018] — advocate qualitative description of demographic composition. The GRI provides the quantitative counterpart: a standardized score that enables comparison across datasets and tracking of composition changes over time.

The connection to ML fairness is direct. The GRI measures what might be called *demographic parity of sampling probability*: a GRI of 1.0 means every demographic group is sampled in proportion to its population share. This is precisely the condition under which a dataset drawn from the population would, in expectation, treat all groups equally in training data representation. The TVD underlying the GRI is related to, though distinct from, the Maximum Mean Discrepancy (MMD) commonly used for distribution shift detection in ML: TVD operates on discrete categorical distributions while MMD works in continuous kernel-defined feature spaces.

For ML applications, the framework would require two adaptations: (1) benchmarks appropriate to the target population (which may not be the world — a medical imaging dataset should be benchmarked against the relevant patient population), and (2) potential extension to handle the higher-dimensional attribute spaces common in ML contexts. We discuss the scalability challenges of high-dimensional demographic spaces in Section 7.7.

---

## 6. Practical Implementation

### 6.1 The `gri` Python Library

The GRI framework is implemented as an open-source Python library (`gri`) comprising 16 modules organized into four layers:

**Calculation Layer**: Core metric computation
- `calculator.py`: GRI and Diversity Score
- `strategic_index.py`: SRI computation
- `simulation.py`: Monte Carlo maximum possible scores and efficiency ratios

**Analysis Layer**: Diagnostic tools
- `analysis.py`: Segment deviations, alignment checking, impact analysis
- `scorecard.py`: Multi-dimensional scorecard generation
- `benchmark_simplifier.py`: Benchmark simplification for high-cardinality dimensions

**Data Layer**: Input/output
- `data_loader.py`: Benchmark and survey data loading with format detection
- `config.py`: YAML-based configuration management
- `validation.py`: Survey data validation

**Presentation Layer**: Output
- `visualization.py`: Six publication-quality plot types
- `reports.py`: Text, CSV, JSON, and Excel report generation

### 6.2 API Design

The library exposes two API surfaces for different workflows.

**Functional API** for scripted pipelines:

```python
from gri import calculate_gri, calculate_diversity_score, load_benchmark_suite

# Load benchmarks
benchmarks = load_benchmark_suite()

# Calculate GRI for a single dimension
gri_score = calculate_gri(
    survey_df,
    benchmarks['country_gender_age'],
    strata_cols=['country', 'gender', 'age_group']
)

# Calculate diversity coverage
diversity = calculate_diversity_score(
    survey_df,
    benchmarks['country_gender_age'],
    strata_cols=['country', 'gender', 'age_group']
)
```

**Object-oriented API** for interactive analysis:

```python
from gri import GRIAnalysis

# One-line initialization with automatic benchmark loading
analysis = GRIAnalysis.from_survey_file('data/gd3_participants.csv')

# Full scorecard with Monte Carlo max scores
scorecard = analysis.calculate_scorecard(
    dimensions='all',
    include_max_possible=True,
    n_simulations=1000
)

# Diagnostic visualization
analysis.plot_scorecard(save_to='figures/gd3_scorecard.png')
analysis.plot_top_deviations('Country × Gender × Age', n=20)

# Identify highest-impact segments for improvement
top_gaps = analysis.get_top_segments(
    'Country × Gender × Age',
    n=10,
    segment_type='under'
)

# Generate comprehensive report
analysis.generate_report(output_file='gd3_report.txt')
```

### 6.3 Best Practices

**Pre-survey planning.** Use Monte Carlo simulation to set realistic GRI targets for the planned sample size and identify the minimum sample size needed for target representativeness:

```python
from gri import monte_carlo_max_scores, load_benchmark_suite

benchmarks = load_benchmark_suite()
# What's achievable at N=500?
max_scores = monte_carlo_max_scores(
    benchmarks['country_gender_age'],
    sample_size=500,
    n_simulations=1000
)
# max_scores['max_gri_mean'] ≈ 0.691
```

**During data collection.** Compute GRI in real-time as responses accumulate. The segment deviation analysis identifies which demographic groups are most needed:

```python
from gri import calculate_dimension_impact

impact = calculate_dimension_impact(
    current_sample,
    benchmarks['country_religion'],
    ['country', 'religion'],
    n_targets=10
)
# Returns: segments where additional recruitment would most improve GRI
```

**Post-hoc reporting.** Generate a complete representativeness scorecard alongside survey results. Report GRI for distributional fidelity and the efficiency ratio to contextualize scores against structural constraints:

```python
from gri import GRIScorecard

scorecard_gen = GRIScorecard()
scorecard = scorecard_gen.generate_scorecard(
    survey_df,
    base_path='data/'
)
print(scorecard_gen.format_scorecard(scorecard, format='markdown'))
# Scorecard includes GRI, Max GRI, Efficiency Ratio, Diversity Score, and SRI
```

---

## 7. Limitations and Future Work

### 7.1 Benchmark Data Staleness

The GRI is only as accurate as its population benchmarks, and the religious composition data from Pew dates to 2010 — a significant limitation for a framework presented in 2024. In 14 years, religious demographics have shifted meaningfully: rapid secularization in Western Europe and East Asia, growth of "spiritual but not religious" identities in many developed nations, the expansion of Pentecostalism in Sub-Saharan Africa and Latin America, and complex dynamics around religious expression in China. The 2010 benchmark likely overstates the globally affiliated religious population and understates the unaffiliated share.

Why not use more recent data? Pew published updated religious projections in 2015, but these are projections (model-based) rather than observed data, and they are not available in the country-by-religion disaggregated format required for cross-classification. The 2010 dataset remains the most comprehensive *observed* cross-national religious demography available. This is an unsatisfying answer — and it illustrates a broader challenge: the GRI's utility is constrained by the availability of high-quality, globally comparable demographic benchmarks.

We recommend three practices: (1) always report the benchmark vintage alongside GRI scores ("GRI computed against Pew 2010 religious benchmarks"); (2) update benchmarks on a 5-year cycle as new sources become available; and (3) conduct sensitivity analysis by perturbing benchmark proportions to assess how robust GRI scores are to plausible demographic shifts. The urbanization data (2018) is more current but will also age. The age/gender data (UN WPP 2023) is the most current benchmark and also the least subject to rapid change.

### 7.2 Equal Weighting Across Dimensions

The current framework reports separate scores for each dimension but does not prescribe how to aggregate them into a single composite. An unweighted average of Country × Gender × Age (GRI ≈ 0.31), Country × Religion (GRI ≈ 0.49), and Country × Environment (GRI ≈ 0.36) gives approximately 0.39. But should all dimensions be weighted equally? A health survey might weight age and gender more heavily; a study of religious attitudes might weight religious composition higher. We deliberately leave aggregation weighting to the researcher, treating the multi-dimensional scorecard as the primary output rather than a single composite score.

### 7.3 Continuous Variables

The GRI requires categorical strata. Age, which is naturally continuous, is discretized into 6 brackets (18–24 through 65+). This discretization loses information — a sample with mean age 30 and a sample with mean age 35 might have identical GRI scores if the discretized distributions are the same. Extending the framework to continuous demographics would require kernel-density-based distance metrics (e.g., integrated squared error) and substantially different benchmark data. This remains a direction for future work.

### 7.4 Intersectionality Beyond Defined Strata

The GRI evaluates the joint distribution of pre-specified dimensions (e.g., Country × Gender × Age) but cannot capture intersectionalities not encoded in the strata. A sample might have excellent Country × Gender × Age representativeness but systematically exclude disabled individuals, indigenous populations, or linguistic minorities. The framework is extensible — any categorical demographic variable with a population benchmark can be added as a new dimension — but the choice of *which* dimensions to include is a substantive decision with equity implications.

### 7.5 The 1/N Threshold and Diversity Score Non-Monotonicity

The Diversity Score's relevance threshold of $X = 1/N$ is principled (expectation of at least one observation under the Poisson approximation to multinomial sampling) but not uniquely correct. At $X = 1/N$, a sample of 1,000 considers 376 of 2,699 Country × Gender × Age strata "relevant." At $X = 2/N$, only those with expected count ≥ 2 would be relevant — a more conservative criterion. At $X = 1/(2N)$, more strata become relevant, potentially inflating the diversity score by including strata that are unlikely to appear in any finite sample. We selected $1/N$ based on Monte Carlo validation showing it best aligns theoretical and observed coverage rates, but researchers should report their threshold alongside the score.

An important consequence of the $1/N$ threshold is that the Diversity Score is **not necessarily monotone in sample size**. As $N$ increases, the threshold $1/N$ decreases, making more strata "relevant." If a larger sample does not cover these newly relevant strata, the denominator increases faster than the numerator, and the Diversity Score can *decrease* even as the sample grows. This non-monotonicity is semantically correct — a larger sample *should* be held to higher coverage standards — but it may confuse practitioners who expect "bigger sample → better score." For the same reason, Diversity Scores should not be directly compared across surveys of substantially different sizes without accounting for the threshold difference. For ML datasets with millions of items, $1/N$ becomes vanishingly small, making virtually all strata "relevant" and the Diversity Score effectively a simple coverage fraction — which may actually be the appropriate metric at that scale.

### 7.6 Population Benchmark Uncertainty

The GRI treats population benchmarks as ground truth, but they are themselves estimates with uncertainty — particularly for countries with limited census infrastructure. A fully Bayesian treatment that propagates benchmark uncertainty into GRI confidence intervals — treating $q_i$ as random variables with distributions reflecting census quality — remains an important direction for future work.

### 7.7 Scalability with Many Dimensions

Adding dimensions multiplicatively increases the number of strata. Country × Gender × Age already has 2,699 strata; adding Religion would create Country × Gender × Age × Religion with potentially tens of thousands. At this resolution, virtually all strata would be empty in any feasible sample, and the GRI would approach a universal constant determined by sample size rather than sampling quality.

This is a fundamental limitation, not merely an implementation challenge. In the ML fairness literature, the tension between intersectional representativeness (ensuring that *women of color in rural areas of specific age groups* are represented, not just that each marginal dimension is covered) and the curse of dimensionality is well-recognized. The pairwise scorecard approach addresses this by evaluating each pair of crossed dimensions separately. This provides a useful multi-resolution view but does lose information about higher-order interactions: a sample could score well on Country × Gender and Country × Age while systematically excluding young women from specific countries.

Extending the framework to higher-dimensional intersections would require either: (a) dramatically larger sample sizes (making the approach infeasible for typical surveys), (b) approximation methods such as random projections or hashing of high-dimensional strata into lower-dimensional spaces, or (c) parametric approaches that model the joint distribution rather than evaluating every cell. These remain directions for future work. For practical purposes, the pairwise scorecard captures the most important representativeness signals — the three-way cross of Country × Gender × Age being the most demanding dimension we evaluate.

### 7.8 Subnational Variation

The GRI framework as presented uses global population benchmarks and measures representativeness relative to the world population. Most survey practitioners, however, work with national surveys where subnational representativeness is the primary concern — whether a sample of Nigerians adequately represents regional, ethnic, and socioeconomic variation within Nigeria. The framework is technically applicable at any geographic scope (swap global benchmarks for national census data), but the current library ships only with global benchmarks. Integrating subnational benchmark data — from national censuses, Demographic and Health Surveys, or administrative records — would substantially broaden the framework's practical utility and is a priority for future development.

---

## 8. Conclusion

The Global Representativeness Index transforms a vague question — "How representative is this survey?" — into a precise, measurable quantity. By grounding representativeness measurement in Total Variation Distance, the GRI provides researchers with a metric that is mathematically rigorous, empirically interpretable, and actionable.

The empirical application to six waves of the Global Dialogues survey reveals a sobering reality: a purposive online survey spanning 60+ countries achieves Country × Gender × Age GRI scores of only 0.29–0.37, capturing less than 40% of the theoretically achievable representativeness at its sample size. The primary drivers are geographic concentration (oversampling of a few countries at the expense of populous nations like China) and structural modality bias (online surveys systematically underrepresent rural populations). While these findings are specific to the Global Dialogues, the underlying challenges — integer allocation constraints, combinatorial explosion of strata, urban-digital bias — are endemic to global survey research broadly.

What changes if researchers adopt the GRI? Three things. First, **transparency**: every survey can report a standardized, comparable representativeness score alongside its results, enabling consumers of research to calibrate their confidence in "global" findings. Second, **optimization**: the segment-level decomposition and efficiency analysis identify exactly which demographic gaps matter most, guiding recruitment strategy. Third, **accountability**: funders and policymakers can set minimum representativeness targets for research that claims to represent global populations, just as they set minimum sample size requirements.

The complementary metrics extend this toolkit: the SRI for designing surveys that maximize statistical power across populations, the efficiency ratio for contextualizing scores against structural constraints, and the design effect for quantifying the inferential cost of distributional mismatch. Together, these metrics span the lifecycle of survey research — design (SRI, Monte Carlo max scores), execution (real-time GRI monitoring, segment deviation analysis), and evaluation (GRI, efficiency ratio, design effect, effective sample size).

The framework is released as open-source software with authoritative population benchmarks from the United Nations and Pew Research Center. We invite the survey methodology community to adopt, critique, and extend it.

---

## References

[Brick and Williams, 2013] Brick, J.M. and Williams, D. (2013). "Explaining rising nonresponse rates in cross-sectional surveys." *The ANNALS of the American Academy of Political and Social Science*, 645(1), 36–59.

[Groves, 2006] Groves, R.M. (2006). "Nonresponse rates and nonresponse bias in household surveys." *Public Opinion Quarterly*, 70(5), 646–675.

[Groves and Peytcheva, 2008] Groves, R.M. and Peytcheva, E. (2008). "The impact of nonresponse rates on nonresponse bias: A meta-analysis." *Public Opinion Quarterly*, 72(2), 167–189.

[Horvitz and Thompson, 1952] Horvitz, D.G. and Thompson, D.J. (1952). "A generalization of sampling without replacement from a finite universe." *Journal of the American Statistical Association*, 47(260), 663–685.

[Kish, 1965] Kish, L. (1965). *Survey Sampling*. John Wiley & Sons.

[Neyman, 1934] Neyman, J. (1934). "On the two different aspects of the representative method: The method of stratified sampling and the method of purposive selection." *Journal of the Royal Statistical Society*, 97(4), 558–625.

[Rubin, 2001] Rubin, D.B. (2001). "Using propensity scores to help design observational studies: Application to the tobacco litigation." *Health Services and Outcomes Research Methodology*, 2, 169–188.

[Schouten, Cobben, and Bethlehem, 2009] Schouten, B., Cobben, F., and Bethlehem, J. (2009). "Indicators for the representativeness of survey response." *Survey Methodology*, 35(1), 101–113.

[Stuart, 2010] Stuart, E.A. (2010). "Matching methods for causal inference: A review and a look forward." *Statistical Science*, 25(1), 1–21.

[Gebru et al., 2021] Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J.W., Wallach, H., Daumé III, H., and Crawford, K. (2021). "Datasheets for datasets." *Communications of the ACM*, 64(12), 86–92.

[Mitchell et al., 2019] Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I.D., and Gebru, T. (2019). "Model cards for model reporting." *Proceedings of the Conference on Fairness, Accountability, and Transparency*, 220–229.

[Le Cam, 1986] Le Cam, L. (1986). *Asymptotic Methods in Statistical Decision Theory*. Springer.

[Tsybakov, 2009] Tsybakov, A.B. (2009). *Introduction to Nonparametric Estimation*. Springer.

[Devroye and Györfi, 1985] Devroye, L. and Györfi, L. (1985). *Nonparametric Density Estimation: The L1 View*. John Wiley & Sons.

[Buolamwini and Gebru, 2018] Buolamwini, J. and Gebru, T. (2018). "Gender shades: Intersectional accuracy disparities in commercial gender classification." *Proceedings of the Conference on Fairness, Accountability and Transparency*, 77–91.

[Bender and Friedman, 2018] Bender, E.M. and Friedman, B. (2018). "Data statements for natural language processing: Toward mitigating system bias and enabling better science." *Transactions of the Association for Computational Linguistics*, 6, 587–604.

[UNESCO, 2021] UNESCO (2021). *Recommendation on the Ethics of Artificial Intelligence*. Adopted by the General Conference at its 41st session, 23 November 2021. Available at: https://unesdoc.unesco.org/ark:/48223/pf0000381137

[European Parliament, 2024] European Parliament and Council of the European Union (2024). Regulation (EU) 2024/1689 Laying Down Harmonised Rules on Artificial Intelligence (AI Act). *Official Journal of the European Union*, L series, 12 July 2024. Available at: https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng

[Haerpfer et al., 2022] Haerpfer, C., Inglehart, R., Moreno, A., Welzel, C., Kizilova, K., Diez-Medrano, J., Lagos, M., Norris, P., Ponarin, E., and Puranen, B. (eds.) (2022). *World Values Survey: Round Seven — Country-Pooled Datafile Version 5.0*. Madrid, Spain & Vienna, Austria: JD Systems Institute & WVSA Secretariat. doi:10.14281/18241.24

[Gallup, 2024] Gallup (2024). *Worldwide Research Methodology and Codebook*. Gallup World Poll technical documentation. Available at: https://www.gallup.com/178667/gallup-world-poll-work.aspx

---

## Appendix A: Mathematical Proofs

### A.1 Proof of GRI Bounds

**Theorem.** For any two discrete probability distributions $P = (p_1, \ldots, p_K)$ and $Q = (q_1, \ldots, q_K)$ over $K$ categories, the Global Representativeness Index satisfies $0 \leq \text{GRI}(P, Q) \leq 1$.

**Proof.** Since GRI $= 1 - \text{TVD}(P, Q)$, it suffices to show $0 \leq \text{TVD} \leq 1$.

*Lower bound.* $\text{TVD} = \frac{1}{2}\sum_i |p_i - q_i| \geq 0$ since each term is non-negative. Equality holds iff $p_i = q_i$ for all $i$.

*Upper bound.* By the triangle inequality applied to each term:
$$\sum_i |p_i - q_i| \leq \sum_i (p_i + q_i) = \sum_i p_i + \sum_i q_i = 1 + 1 = 2$$

Therefore $\text{TVD} \leq 1$. Equality holds iff the supports of $P$ and $Q$ are disjoint: $p_i > 0 \implies q_i = 0$ and $q_i > 0 \implies p_i = 0$. In this case $\sum_i |p_i - q_i| = \sum_i p_i + \sum_i q_i = 2$. □

### A.2 Monotonicity of GRI Under Reallocation

**Theorem.** Let $P = (p_1, \ldots, p_K)$ be a sample distribution and $Q = (q_1, \ldots, q_K)$ the target. If we modify $P$ by transferring mass $\delta > 0$ from stratum $j$ (where $p_j > q_j$) to stratum $k$ (where $p_k < q_k$), with $\delta \leq \min(p_j - q_j, q_k - p_k)$, then $\text{GRI}$ increases.

**Proof.** The new distribution $P' = P$ except $p'_j = p_j - \delta$ and $p'_k = p_k + \delta$. The change in TVD is:
$$\Delta\text{TVD} = \frac{1}{2}(|p'_j - q_j| + |p'_k - q_k| - |p_j - q_j| - |p_k - q_k|)$$

Since $p_j > q_j$ and $\delta \leq p_j - q_j$, we have $|p'_j - q_j| = p_j - \delta - q_j = |p_j - q_j| - \delta$. Similarly, since $p_k < q_k$ and $\delta \leq q_k - p_k$, we have $|p'_k - q_k| = q_k - p_k - \delta = |p_k - q_k| - \delta$. Thus $\Delta\text{TVD} = -\delta < 0$, so GRI increases. □

**Remark.** The constraint $\delta \leq \min(p_j - q_j, q_k - p_k)$ ensures the signs of the deviations do not flip. In the general case where $\delta$ exceeds this bound, the reallocation still reduces TVD up to the point where either $p'_j = q_j$ or $p'_k = q_k$, after which further reallocation reverses the direction of deviation in that stratum. GRI is therefore monotonically increasing for reallocations *toward* the target distribution, but can decrease for overshooting reallocations.

### A.3 Relationship Between TVD and Other Distances

TVD relates to other distributional distances as follows. Let $H(P,Q)$ denote the Hellinger distance and $D_{\text{KL}}(P \| Q)$ the KL divergence. Then:

$$H^2(P,Q) \leq \text{TVD}(P,Q) \leq H(P,Q)\sqrt{2}$$

$$\text{TVD}(P,Q) \leq \sqrt{\frac{1}{2} D_{\text{KL}}(P \| Q)}$$

(Pinsker's inequality)

These relationships establish that TVD is bounded below by the squared Hellinger distance and above by a function of KL divergence, placing it in a well-characterized metric space.

---

## Appendix B: Pseudocode for Core Algorithms

### B.1 GRI Calculation

```
function CALCULATE_GRI(sample, benchmark, strata_columns):
    // Compute sample proportions
    sample_counts ← GROUP_AND_COUNT(sample, strata_columns)
    sample_proportions ← sample_counts / SUM(sample_counts)

    // Compute benchmark proportions
    benchmark_proportions ← NORMALIZE(benchmark[strata_columns, 'proportion'])

    // Outer join to handle strata present in only one distribution
    merged ← OUTER_JOIN(sample_proportions, benchmark_proportions, on=strata_columns)
    merged ← FILL_MISSING(merged, 0)

    // Total Variation Distance
    tvd ← 0.5 * SUM(ABS(merged.sample_prop - merged.benchmark_prop))

    return 1.0 - tvd
```

### B.2 Diversity Score Calculation

```
function CALCULATE_DIVERSITY(sample, benchmark, strata_columns, N):
    threshold ← 1.0 / N

    // Identify relevant strata (population proportion > threshold)
    relevant ← benchmark[benchmark.proportion > threshold]

    // Identify represented relevant strata
    sample_strata ← UNIQUE_STRATA(sample, strata_columns)
    represented ← relevant ∩ sample_strata

    return |represented| / |relevant|
```

### B.3 Monte Carlo Maximum GRI

```
function MONTE_CARLO_MAX_GRI(benchmark, sample_size, n_simulations):
    proportions ← NORMALIZE(benchmark.proportion)
    results ← []

    for sim in 1..n_simulations:
        // Optimal allocation with stochastic rounding
        ideal ← proportions * sample_size
        allocation ← []
        for each stratum i:
            if ROUND(ideal[i]) > 0:
                allocation[i] ← ROUND(ideal[i])  // deterministic
            else:
                allocation[i] ← BERNOULLI(ideal[i])  // probabilistic

        // Adjust to exact sample size
        ADJUST_TOTAL(allocation, sample_size)

        // Compute GRI for this allocation
        sample_prop ← allocation / sample_size
        gri ← 1 - 0.5 * SUM(ABS(sample_prop - proportions))
        results.APPEND(gri)

    return MEAN(results), STD(results)
```

---

## Appendix C: Extended Scorecard Tables

### C.1 Complete GRI Scorecard: GD1–GD6 Across All 13 Dimensions

| Dimension | GD1 (N=1280) | GD2 (N=1105) | GD3 (N=971) | GD4 (N=1050) | GD5 (N=1057) | GD6 (N=1037) |
|-----------|:------:|:------:|:------:|:------:|:------:|:------:|
| Country × Gender × Age | 0.293 | 0.282 | 0.374 | 0.319 | 0.301 | 0.292 |
| Country × Religion | 0.471 | 0.474 | 0.515 | 0.518 | 0.484 | 0.481 |
| Country × Environment | 0.369 | 0.339 | 0.387 | 0.390 | 0.354 | 0.345 |
| Country | 0.516 | 0.502 | 0.539 | 0.571 | 0.527 | 0.519 |
| Region × Gender × Age | 0.545 | 0.543 | 0.580 | 0.577 | 0.563 | 0.559 |
| Region × Religion | 0.597 | 0.587 | 0.639 | 0.647 | 0.609 | 0.621 |
| Region × Environment | 0.537 | 0.507 | 0.562 | 0.576 | 0.520 | 0.518 |
| Region | 0.745 | 0.739 | 0.791 | 0.799 | 0.738 | 0.734 |
| Continent | 0.832 | 0.830 | 0.886 | 0.883 | 0.773 | 0.802 |
| Religion | 0.817 | 0.819 | 0.833 | 0.826 | 0.813 | 0.806 |
| Environment | 0.629 | 0.623 | 0.642 | 0.628 | 0.635 | 0.620 |
| Age Group | 0.656 | 0.684 | 0.706 | 0.723 | 0.746 | 0.756 |
| Gender | 0.989 | 0.990 | 0.996 | 0.979 | 0.986 | 0.995 |

### C.2 Diversity Scores: GD1–GD6 Across All 13 Dimensions

| Dimension | GD1 | GD2 | GD3 | GD4 | GD5 | GD6 |
|-----------|:------:|:------:|:------:|:------:|:------:|:------:|
| Country × Gender × Age | 0.464 | 0.458 | 0.470 | 0.476 | 0.464 | 0.458 |
| Country × Religion | 0.538 | 0.521 | 0.453 | 0.487 | 0.496 | 0.521 |
| Country × Environment | 0.434 | 0.414 | 0.394 | 0.393 | 0.372 | 0.372 |
| Country | 0.490 | 0.471 | 0.828 | 0.490 | 0.461 | 0.471 |
| Region × Gender × Age | 0.696 | 0.641 | 0.625 | 0.652 | 0.663 | 0.669 |
| Region × Religion | 0.852 | 0.852 | 0.824 | 0.852 | 0.796 | 0.815 |
| Region × Environment | 0.816 | 0.816 | 0.789 | 0.789 | 0.789 | 0.763 |
| Region | 0.950 | 0.950 | 0.850 | 0.900 | 0.900 | 0.900 |
| Continent | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Religion | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Environment | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Age Group | 1.000 | 1.000 | 1.000 | 0.833 | 1.000 | 1.000 |
| Gender | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

### C.3 Maximum Achievable GRI by Sample Size (Monte Carlo, 1,000 simulations)

| Dimension | N=100 | N=250 | N=500 | N=1000 | N=2000 |
|-----------|:-----:|:-----:|:-----:|:------:|:------:|
| Country × Gender × Age | 0.430 | 0.581 | 0.691 | 0.792 | 0.873 |
| Country × Religion | 0.721 | 0.839 | 0.898 | 0.938 | 0.965 |
| Country × Environment | 0.714 | 0.844 | 0.906 | 0.950 | 0.976 |

---

## Appendix D: Data Availability Statement

**Software.** The `gri` Python library is available at [repository URL] under an open-source license. Installation: `pip install -e .` from the repository root.

**Benchmark Data.** All population benchmark data is included in the repository under `data/raw/benchmark_data/`:
- UN World Population Prospects 2023 (age × gender by country)
- Pew Research Center Global Religious Landscape 2010 (religion by country)
- UN World Urbanization Prospects 2018 (urban/rural by country)

Sources and download links are documented in `data/raw/benchmark_data/Sources.csv`.

**Survey Data.** The Global Dialogues survey data used in the empirical analysis is available via the project's data repository. Processed scorecard results are included in `analysis_output/scorecards/`.

**Replication.** All results in this paper can be reproduced by running the GRI scorecard generation scripts against the included benchmark and survey data. See the repository README for instructions.
