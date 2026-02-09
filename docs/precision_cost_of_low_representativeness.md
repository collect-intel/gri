# The Precision Cost of Low Representativeness

## Why the GRI Matters Beyond Distributional Aesthetics

A natural objection to the Global Representativeness Index is: **"So the sample doesn't mirror the population — just apply post-stratification weights and move on. Why do we need a metric for this?"**

This document explains why that objection fails. The short answer: **reweighting fixes bias but destroys precision.** A low-GRI sample, even after optimal reweighting, produces less precise estimates than a higher-GRI sample of the same size. The GRI quantifies how much statistical precision a survey wastes through poor demographic allocation.

---

## The Reweighting Argument (and Why It's Incomplete)

Post-stratification reweighting is standard survey practice. If stratum $i$ constitutes proportion $q_i$ of the population but proportion $p_i$ of the sample, assigning each respondent in stratum $i$ the weight $w_i = q_i / p_i$ corrects the demographic imbalance. The weighted sample mean is an unbiased estimator of the population mean.

This is real and useful. But it addresses only the **point estimate** — the center of the confidence interval. It says nothing about the **width** of that interval — how precisely we actually know the answer.

The precision of a weighted estimate depends on how extreme the weights are. And weight extremity is directly determined by how far the sample's demographic composition deviates from the population — exactly what the GRI measures.

---

## Design Effect and Effective Sample Size

The **design effect** (deff) quantifies how much less precise a weighted estimate is compared to a simple random sample of the same size. Under post-stratification weighting:

$$\text{deff} = 1 + \text{CV}^2(w)$$

where $\text{CV}(w)$ is the coefficient of variation of the weights $w_i = q_i / p_i$. When the sample perfectly mirrors the population ($p_i = q_i$ for all $i$), all weights equal 1, CV = 0, and deff = 1 — no precision loss. As the sample deviates from the population, weights become more extreme, CV increases, and deff grows.

The **effective sample size** is:

$$N_{\text{eff}} = \frac{N}{\text{deff}} = \frac{N}{1 + \text{CV}^2(w)}$$

This is the number of respondents from a simple random sample that would give you the same precision as your actual weighted sample of $N$ respondents.

### A Concrete Example

Consider a survey of India (population ~1.4 billion) and Sri Lanka (population ~22 million). The combined population is roughly 98.5% Indian, 1.5% Sri Lankan.

**Scenario A — Proportional sample (high GRI):**
- 1,000 respondents: 985 Indian, 15 Sri Lankan
- Weights: all ≈ 1.0
- Design effect ≈ 1.0
- Effective N ≈ 1,000
- Sri Lankan opinion estimated from 15 people (noisy, but proportional to their share)

**Scenario B — Skewed sample (low GRI):**
- 1,000 respondents: 999 Indian, 1 Sri Lankan
- Weight for the 1 Sri Lankan: $0.015 / 0.001 = 15$
- Weight for Indians: $0.985 / 0.999 ≈ 0.986$
- CV of weights is large because of the single extreme weight
- Design effect > 1
- Effective N < 1,000
- The entire Sri Lankan contribution rests on one person's opinion, amplified 15×

**Scenario C — Extremely skewed sample (very low GRI):**
- 1,000 respondents: 500 Indian, 500 Sri Lankan
- Wait — this is oversampling Sri Lanka massively (500 people for 1.5% of population)
- Weight for Sri Lankans: $0.015 / 0.5 = 0.03$
- Weight for Indians: $0.985 / 0.5 = 1.97$
- Half the sample gets weight 0.03 (essentially discarded) while half gets weight ~2
- Design effect ≈ 2.0
- Effective N ≈ 500
- You spent budget on 500 Sri Lankan respondents whose information is almost entirely wasted after reweighting

The key insight: **in both Scenarios B and C, reweighting produces an unbiased point estimate. But the confidence interval is wider than in Scenario A.** The misallocation wastes data — either by leaving strata too small to estimate reliably (Scenario B) or by oversampling strata whose excess information gets downweighted away (Scenario C).

---

## Why Reweighting Can't Fully Compensate for Low GRI

There are four distinct reasons why "just reweight" is insufficient:

### 1. Reweighting inflates variance

The variance of a post-stratified weighted mean is approximately:

$$\text{Var}(\bar{y}_w) = \sum_i \frac{q_i^2 \cdot \sigma_i^2}{n_i}$$

where $\sigma_i^2$ is the within-stratum variance and $n_i$ is the number of respondents in stratum $i$. When $n_i$ is small (underrepresented strata), $q_i^2 / n_i$ is large, and that stratum's contribution to total variance dominates — even if $q_i$ itself is modest. Reweighting amplifies the noise from small strata.

### 2. Empty strata are uncorrectable

Reweighting requires at least one respondent per stratum. For strata with $n_i = 0$, no weight can recover the missing information. The Diversity Score captures this: when it shows that 54% of relevant Country × Gender × Age strata are unrepresented, that's 54% of the demographic space where reweighting is mathematically impossible. The analyst must either drop those strata (introducing a different bias), impute (introducing model assumptions), or accept a gap. None of these is "just reweighting."

### 3. Extreme weights increase model dependence

With 2 respondents representing an entire stratum, the implicit assumption is that those 2 people are representative of everyone in that stratum. This assumption is untestable and often wrong — the 2 Sri Lankans who happened to take an online survey are probably urban, English-speaking, and internet-connected, which is not representative of Sri Lanka. As weights grow more extreme, the estimate becomes increasingly sensitive to who exactly ended up in each small stratum. The estimate is technically "unbiased" only under the assumption that respondents within each stratum are randomly drawn from that stratum — an assumption that becomes less credible as strata shrink.

### 4. Reweighting treats the symptom, not the cause

A survey with GRI = 0.32 that gets reweighted to produce an unbiased point estimate is not equivalent to a survey with GRI = 0.70 that needs minimal reweighting. The first survey's estimates are fragile — sensitive to which specific individuals happened to respond, to the weighting model chosen, and to stratum definitions. The second survey's estimates are robust — supported by enough respondents in each stratum that the within-stratum averages are stable. The GRI measures this robustness directly: it tells you how far your raw data is from the target distribution, and therefore how much corrective work (and fragility) the reweighting must introduce.

---

## The Marginal Value of Additional Respondents

The precision cost framework also explains why proportional representation isn't the end of the story — and why the SRI's square-root allocation target exists.

The marginal reduction in total estimation variance from adding one more respondent to stratum $i$ is:

$$\frac{\partial \text{Var}(\bar{y}_w)}{\partial n_i} \propto -\frac{q_i^2 \cdot \sigma_i^2}{n_i^2}$$

This means the marginal value of an additional respondent is:

- **High** when $n_i$ is small — going from 2 to 3 respondents in a stratum matters far more than going from 500 to 501
- **Low** when $n_i$ is large — additional respondents in already-well-sampled strata contribute almost nothing to precision
- **Proportional to $q_i^2$** — strata that are larger in the population deserve more investment because their estimates affect more of the population-level inference

This creates a tension. Pure proportional allocation (the GRI's implicit target) assigns $n_i \propto q_i$, giving large strata many respondents (where marginal value is low) and small strata few respondents (where marginal value is high but $n_i$ is too small for reliable estimation). The SRI's square-root target ($s_i^* \propto \sqrt{q_i}$) redistributes sample toward smaller strata, improving the worst-case estimation precision across all strata.

But regardless of whether you target proportional or square-root allocation, the key insight is the same: **sample allocated to the wrong strata is wasted.** An overrepresented stratum has diminishing marginal returns, while an underrepresented stratum has high marginal value per additional respondent. The GRI measures the degree of this misallocation.

---

## Connecting GRI to Effective Sample Size: The Proposed Analysis

### Goal

Demonstrate empirically that low GRI corresponds to low effective sample size — that the GRI predicts how much statistical precision a survey wastes through poor demographic allocation.

### Method

For each Global Dialogues wave (GD1–GD6):

1. **Compute post-stratification weights** for the Country × Gender × Age dimension:
   - For each respondent, $w_i = q_i / p_i$ where $q_i$ is the population proportion and $p_i$ is the sample proportion of their stratum
   - Strata with zero population proportion are excluded; strata with zero sample members cannot be weighted

2. **Compute the design effect:**
   - $\text{deff} = 1 + \text{CV}^2(w)$ where CV is the coefficient of variation of the respondent-level weights

3. **Compute effective sample size:**
   - $N_{\text{eff}} = N / \text{deff}$

4. **Report the relationship between GRI and $N_{\text{eff}}$:**
   - Across waves, show that lower GRI corresponds to lower effective N
   - Quantify the "wasted" respondents: $N - N_{\text{eff}}$

5. **For a key survey question** (a poll question with clear response options):
   - Compute the unweighted response distribution
   - Compute the weighted response distribution
   - Compute the confidence interval of the weighted estimate
   - Compare to the confidence interval that would result from a sample with higher GRI (via simulation or analytical approximation)

### Expected Results

Based on the GD data characteristics (GRI ≈ 0.31 for Country × Gender × Age, with extreme geographic concentration in a few countries):

- Design effects are likely in the range of 3–8, meaning effective sample sizes of 130–350 from nominal samples of ~1,000
- The confidence interval for any weighted population mean will be 2–3× wider than for a perfectly representative sample of the same size
- The "precision cost" can be stated as: "This survey's 1,050 respondents carry the statistical precision of approximately [X] respondents from a well-designed proportional sample"

### The Punchline for Funders and Policymakers

The GRI translates directly into budget efficiency:

> A survey with GRI = 0.32 and N = 1,050 has an effective sample size of ~[X] after post-stratification. Achieving the same effective precision with a GRI of 0.60 would require only ~[Y] respondents. **Low representativeness doesn't just bias results — it wastes the budget spent collecting redundant information from overrepresented groups while leaving underrepresented groups too noisy to contribute meaningfully, even after reweighting.**

This reframes the GRI from a metric of "distributional aesthetics" to a metric of **statistical efficiency**: it tells you how much of your data-collection investment actually contributes to reliable population-level inference.

---

## The "GRI Is Too Harsh" Problem: Max GRI and the Efficiency Ratio

### The Problem

A raw GRI of 0.32 on Country × Gender × Age sounds terrible — 68% of the sample's demographic weight is misallocated. But this number penalizes two fundamentally different things as if they were one:

1. **Structural impossibility.** With N = 1,000 and 2,699 strata, you cannot fill them all proportionally. Hundreds of strata have population proportions below 1/1000, meaning perfect proportional representation would require fractional people. Even an omniscient allocator with unlimited recruitment access achieves only GRI = 0.792 at this sample size. The remaining 0.208 gap from perfect is baked into the math, not a sampling failure.

2. **Allocation failure.** Of the respondents you did recruit, you concentrated too many in Kenya and India and not enough in China and Indonesia. This is a sampling strategy problem that the survey designer could, in principle, fix.

The raw GRI blends these together. A survey designer seeing 0.32 can't tell: "Is this bad because my survey is poorly designed, or because I'd need 50,000 respondents to do better?"

### The Solution: Max GRI and the Efficiency Ratio

The GRI framework already computes the **maximum achievable GRI** via Monte Carlo simulation — the best score a perfectly allocated sample of the same size could achieve. The **efficiency ratio** is the ratio of actual to maximum:

$$\text{Efficiency} = \frac{\text{GRI}_{\text{actual}}}{\text{GRI}_{\text{max}}}$$

For GD4 on Country × Gender × Age:
- GRI = 0.319
- Max GRI = 0.792
- Efficiency = 40.3%

This directly answers: **"Of the representativeness that is achievable at your sample size, how much did you capture?"**

- 40% efficiency means 60% of your representativeness gap is your survey's fault, not the math's fault.
- 100% efficiency means you've done everything possible at your sample size — further improvement requires more respondents, not different respondents.
- The denominator (Max GRI) absorbs the structural penalty entirely, so the numerator measures only what the survey designer controls.

### Why the Efficiency Ratio Should Be Elevated

The efficiency ratio already exists in every scorecard (the `gri_pct_of_max` column), but it's treated as a secondary derived quantity. Given that it directly answers the most common misinterpretation of raw GRI scores — "this number is low, so the survey is bad" vs. "this number is low because the task is hard" — it deserves to be a primary reported metric alongside the raw GRI.

The raw GRI and the efficiency ratio together tell a complete story:

| Raw GRI | Efficiency | Interpretation |
|---------|-----------|---------------|
| Low | Low | Poor allocation AND hard problem — improve strategy first, then consider larger N |
| Low | High | Hard problem, good allocation — you're doing the best you can; need more respondents |
| High | High | Easy problem, good allocation — this dimension is well-represented |
| High | Low | Easy problem, poor allocation — you should be doing much better here |

For the Global Dialogues, the efficiency analysis reveals that Country × Religion has the most room for strategic improvement: the theoretical maximum at N = 1,000 is 0.94, but achieved scores hover around 0.49 — an efficiency of only 52%. The structural ceiling is high, meaning better sampling strategy (not more respondents) is the primary lever.

### Why the Now-Deprecated VWRS Was a Worse Answer to the Same Problem

The Variance-Weighted Representativeness Score (VWRS) was an earlier attempt to solve the same "GRI is too harsh" problem. Rather than normalizing against the theoretical maximum, it addressed the harshness by downweighting deviations in strata with few respondents — using a weight of $w_i = q_i \times SE_i \times r_i$.

This produced dramatically higher scores (VWRS ≈ 0.80 vs. GRI ≈ 0.32 for Country × Gender × Age), but the approach had fundamental problems:

1. **The weight formula was conceptually circular.** The SE depends on $p_i$ (the sample proportion), meaning the weighting scheme changes based on the thing being measured.
2. **The scores were misleading.** VWRS = 0.80 sounds like the survey is doing well, but it reaches that number by downweighting the problem rather than contextualizing it.
3. **It conflated representativeness with opinion estimation.** The SE of a proportion within a stratum is about the reliability of an opinion estimate, not about whether the stratum is proportionally represented. Multiple reviewers flagged this.
4. **It had no theoretical foundation.** Unlike GRI (= 1 - TVD, a well-known quantity) or the efficiency ratio (= ratio against a clearly defined benchmark), the VWRS weighting was ad hoc.

The efficiency ratio solves the problem more cleanly: instead of blurring the structural and allocation components together (VWRS), it separates them. The Max GRI captures the structural ceiling; the efficiency ratio captures how well the survey performs against that ceiling. Both components remain interpretable.

The VWRS is deprecated from the framework. The design effect / effective sample size (discussed in the preceding sections) now serves the role of "translating distributional distance into inferential consequence" — which is what the VWRS was also trying to do, but the design effect does it with standard survey statistics rather than an invented weighting scheme.

---

## But Wait: Does the GRI Measure the Right Thing?

The preceding sections establish that distributional mismatch has a precision cost. A natural follow-up question is sharper: **if what we actually care about is "how efficiently a survey extracts useful information across strata," shouldn't the metric measure THAT directly? Why measure distributional distance (GRI) and then separately compute design effect?**

This is a legitimate challenge, and the answer requires examining what the GRI actually computes versus what we might want it to compute.

### What GRI Measures vs. What We Might Want

The GRI measures: **"How much probability mass needs to be moved to make this sample match the population?"** It uses Total Variation Distance (TVD), the sum of absolute deviations between sample and population proportions.

A different question — arguably the more useful one — is: **"How much useful precision does this sample actually contain for estimating population-level quantities?"** That question is answered by the design effect and effective sample size.

These are related but genuinely different. Here's a case where they diverge:

**Case 1: Many small deviations, no extreme weights.** A survey that slightly oversamples every large country and slightly undersamples every small country. The TVD accumulates across hundreds of strata, producing a GRI of maybe 0.50. But because no individual weight is extreme — large countries go from 18% to 22%, small countries from 0.3% to 0.2% — the design effect might only be 1.3. The survey is distributionally imperfect but inferentially efficient.

**Case 2: Small total deviation, one catastrophic weight.** A survey that matches the population almost perfectly on 98% of strata but has one stratum with 1 respondent representing 5% of the population. The TVD is small (most strata are fine), giving a decent GRI. But that one respondent gets a weight of ~50, dominating the entire weighted estimate. The design effect might be 8+. The survey looks representative but produces terrible estimates.

The mathematical reason for this divergence: the GRI uses TVD, which sums $|p_i - q_i|$ — treating all deviations linearly. The design effect is driven by something closer to **chi-squared divergence**, which sums $q_i^2/p_i$ — treating deviations quadratically and blowing up when any $p_i$ is tiny relative to $q_i$.

TVD says: "A 5% deviation in a big stratum and a 5% deviation in a small stratum are equally bad."

Chi-squared divergence says: "A 5% deviation in a stratum where you have 2 respondents is catastrophically worse than in a stratum where you have 200."

### Should GRI Be Redefined to Use Chi-Squared Divergence?

If we wanted a single metric that directly measures precision cost, we could define:

$$\text{GRI}_{\text{precision}} = \frac{1}{\sum_i q_i^2 / p_i} = \frac{1}{\text{deff}}$$

This ranges from 0 to 1, where 1 means no precision loss (perfect representation). It's bounded, interpretable as "fraction of nominal precision retained," and directly answers the "so what" question.

But this change comes with real costs:

1. **Loss of interpretability.** TVD has a direct prose translation: "31% of probability mass is misallocated." Chi-squared divergence has no equivalent plain-language description. For a metric intended to be communicated to survey practitioners, policymakers, and funders, this loss is significant.

2. **Instability for small strata.** Chi-squared divergence blows up when $p_i \to 0$, making the metric extremely sensitive to whether a rare stratum happens to have 0 vs. 1 respondent. TVD degrades gracefully in these cases.

3. **Different conceptual purpose.** The GRI as currently defined answers "what does this sample look like?" (a diagnostic question about the sample's state). A precision-based metric answers "what can you do with this sample?" (an inferential question about the sample's utility). Both are useful questions — collapsing them into one metric means you can no longer separate them.

### The Case for Keeping GRI as Distributional Distance

The GRI's strength is that it measures **the input** — the demographic state of the sample — without making assumptions about what you're going to do with it. The design effect measures **the consequence** of that state for a specific inferential task (post-stratified estimation of a population mean).

Different survey users care about different things. The complete reporting framework uses six metrics, each answering a distinct question:

| Metric | Question it answers | Primary audience |
|--------|-------------------|-----------------|
| **GRI** | "How far is this sample from the population?" | Everyone — the raw diagnostic |
| **Max GRI** | "How close could the best possible sample at this N get?" | Survey designers — sets realistic expectations |
| **Efficiency Ratio** (GRI / Max GRI) | "How well did this survey use its sample size?" | Survey designers — the actionable number that separates structural limits from allocation failures |
| **Design Effect** | "How much precision does this mismatch cost after reweighting?" | Statisticians — the inferential consequence |
| **Effective N** | "How many respondents' worth of information do I actually have?" | Funders — the budget translation |
| **Diversity Score** | "How many relevant strata are covered at all?" | Everyone — the binary coverage check |

No single metric serves all audiences. The GRI is the right metric for "what does the sample look like?" The efficiency ratio is the right metric for "how well did the survey use its resources, given structural constraints?" The design effect / effective N is the right metric for "what does this cost me in estimation precision?" The Diversity Score is the right metric for "are entire populations missing?"

Together, these six metrics span the full diagnostic: distributional state (GRI), structural context (Max GRI), allocation quality (Efficiency), inferential cost (Design Effect / Effective N), and coverage (Diversity). Each is interpretable on its own, each answers a question the others cannot, and none requires opinion data — they all derive from sample proportions and population benchmarks alone.

### The Case for "GRI + Design Effect" as a Two-Number Report

Rather than merging representativeness and precision into a single metric, the stronger approach is to report both and explain their relationship:

> Survey A: GRI = 0.45, Effective N = 350 / 500 (70% precision retention)
> Survey B: GRI = 0.31, Effective N = 180 / 1,000 (18% precision retention)

The GRI tells you about the distributional state. The effective N ratio tells you about the precision cost. Together they say: "Survey A is closer to the population AND wastes less of its sample." They also allow independent movement: a survey could have moderate GRI but good precision retention (many small deviations, no extreme weights), or vice versa.

The effective N ratio — $N_{\text{eff}} / N$ — is itself a candidate for a named metric. It directly answers "what fraction of your sample budget actually contributes to precision?" and is bounded on [0, 1]. We might call this the **Precision Retention Ratio** or **Sampling Efficiency** (though "efficiency" has existing meaning in survey statistics, so care is needed with naming).

### On the Naming: Is "Representativeness Index" Too Narrow?

The name "Global Representativeness Index" accurately describes what the metric computes: how closely a sample represents the population, measured by distributional distance. The name does not and should not imply that it captures everything one might care about in survey quality.

The paper's job is to explain *why representativeness matters* — not as a distributional aesthetic but as a driver of inferential precision and budget efficiency. The name is fine; the narrative around the name needs to make the precision connection explicit:

> The GRI measures distributional representativeness — how closely the sample mirrors the population. This matters not as an end in itself but because distributional mismatch directly determines the precision cost of post-stratification: surveys with low GRI waste respondents on overrepresented groups while leaving underrepresented groups too noisy to contribute meaningful information, even after reweighting.

---

## Implications for the GRI Paper

This precision-cost argument addresses Reviewer 2's "consequences" critique more powerfully than the original analyses proposed:

1. **It doesn't require cherry-picking survey questions** — the design effect is computed from the weights alone, independent of any specific outcome variable
2. **It preempts the "just reweight" objection** — the entire argument is about what happens *after* reweighting
3. **It connects to money** — funders understand "your 1,000-person survey has the precision of a 200-person survey" in a way they don't understand TVD
4. **It provides a formal link between GRI (a distributional distance metric) and inferential precision (what survey users actually care about)** — bridging the gap that Reviewer 1 identified between "distributional fidelity" and "inferential quality"

---

## Conclusion: What Needs to Change in the GRI Approach

Based on the full reasoning in this document, here is precisely what needs to be edited or added.

### 1. The GRI Definition Does NOT Change

The core metric — $\text{GRI} = 1 - \frac{1}{2}\sum|p_i - q_i|$ — remains as-is. TVD is the right foundation for a communicable representativeness metric. Its interpretability ("X% of probability mass is misallocated") is a genuine advantage over chi-squared divergence or other alternatives that would more directly measure precision but sacrifice the ability to explain the number to non-statisticians. The GRI measures the *state* of the sample (distributional distance from the population), which is a diagnostic property worth measuring in its own right.

### 2. Deprecate VWRS

The Variance-Weighted Representativeness Score is removed from the whitepaper and deprecated in the library. It was an ad hoc attempt to solve two problems — "GRI is too harsh" and "what are the inferential consequences of low GRI" — that are now solved more cleanly by the efficiency ratio and the design effect, respectively.

In the library:
- Mark `calculate_vwrs()` and `calculate_vwrs_from_dataframes()` as deprecated
- Remove VWRS computation from the scorecard pipeline
- Remove the `vwrs` column from scorecard output
- Keep `optimal_allocation()` in `variance_weighted.py` — it implements standard Neyman allocation and is independently useful
- The dedicated VWRS scripts (`calculate_vwrs_all_dimensions.py`, `calculate_vwrs_single_survey.py`) can be archived or removed

In the whitepaper:
- Remove Section 3.5.2 (VWRS definition and discussion) entirely
- Remove VWRS from Table 4 (metric variant comparison)
- Remove VWRS from the scorecard examples and best practices
- A brief footnote or limitation note can acknowledge that an earlier version of the framework included a variance-weighted variant, but this is optional

### 3. Elevate the Efficiency Ratio

The efficiency ratio (GRI / Max GRI) already exists in every scorecard but is treated as a secondary derived column. It should become a primary reported metric:

- In the whitepaper, give the efficiency ratio its own named subsection (not just a paragraph within the Max GRI discussion)
- In scorecard output, ensure the efficiency ratio appears prominently alongside the raw GRI
- In the interpretation guidance, frame the efficiency ratio as the primary "how is my survey doing?" number for practitioners, with raw GRI as the underlying diagnostic

The efficiency ratio is the answer to "GRI is too harsh" — it normalizes for structural constraints and measures only what the survey designer can control.

### 4. Add Design Effect and Effective Sample Size as New Derived Quantities

The `gri` library should compute and report two additional quantities alongside the GRI:

- **Design effect under post-stratification**: $\text{deff} = 1 + \text{CV}^2(w)$ where $w_i = q_i / p_i$
- **Effective sample size**: $N_{\text{eff}} = N / \text{deff}$
- **Precision retention ratio**: $N_{\text{eff}} / N$ (the fraction of the sample budget that contributes to estimation precision)

These are computable from the same inputs as the GRI (sample proportions $p_i$ and population proportions $q_i$), require no opinion data, and are question-independent when computed under worst-case within-stratum variance ($\sigma_i^2 = 0.25$, i.e., binary outcomes). They translate the GRI's distributional finding into inferential consequences.

Implementation: add a `calculate_design_effect()` function (or extend the existing scorecard output) that returns deff, $N_{\text{eff}}$, and the precision retention ratio for each dimension.

### 5. Add a New Section to the Whitepaper: "The Precision Cost of Low Representativeness"

This section (likely Section 5.X, between the current interpretation discussion and the implementation section) should contain:

- **The "just reweight" objection, stated honestly.** Acknowledge that post-stratification can correct point estimates. The paper should not pretend this objection doesn't exist.
- **The four-reason rebuttal** (variance inflation, empty strata, model dependence, fragility). These are standard survey statistics arguments but need to be made explicitly in the paper.
- **A table: GRI, efficiency ratio, design effect, effective N, and precision retention ratio for each GD wave** on the Country × Gender × Age dimension. This is the empirical centerpiece.
- **One worked example** showing that a GD wave's 1,050 respondents carry the effective precision of ~[X] respondents, and that a better-allocated sample of half the size could achieve the same precision. This is the sentence that makes funders pay attention.
- **A paragraph connecting GRI to design effect formally**, noting that while TVD and chi-squared divergence are different functions, they are correlated (both are 0 when $P = Q$ and increase as distributions diverge), so GRI serves as a reliable predictor of precision cost even though it does not directly compute it.

### 6. Update the Scorecard Output

The GRI scorecard currently reports: GRI, Diversity Score, SRI, VWRS, Max GRI, Max Diversity, and efficiency percentages. The revised scorecard removes VWRS and adds the design effect metrics:

| Dimension | GRI | Diversity | Max GRI | Efficiency | deff | N_eff | Precision Retention |
|-----------|-----|-----------|---------|------------|------|-------|-------------------|
| Country × Gender × Age | 0.319 | 0.476 | 0.792 | 40.3% | [X] | [Y] | [Z]% |

This makes the scorecard a complete diagnostic: it tells you what the sample looks like (GRI), how much of the population it reaches (Diversity), how it compares to the theoretical best (Efficiency), and what the inferential cost of its composition is (deff / N_eff / Precision Retention).

The SRI remains in the scorecard — it serves a genuinely different purpose (prospective survey design targeting via square-root allocation) that neither the efficiency ratio nor the design effect replaces.

### 7. Reframe the Paper's Narrative Arc

The current paper's argument is:

> GRI measures representativeness → here are the scores → they're low → the framework is useful for tracking and improving representativeness.

The revised argument should be:

> GRI measures representativeness → here are the scores → they're low → but how much of "low" is structural vs. fixable? (efficiency ratio) → and what does the fixable part cost you in estimation precision? (design effect / effective N) → surveys with low efficiency waste budget on redundant respondents while leaving underrepresented groups too noisy for reliable inference, even after reweighting → the GRI framework is therefore not just a distributional diagnostic but a complete toolkit for understanding and improving the statistical quality of survey samples.

This narrative directly answers all three common objections:
- "That score seems unfairly low" → efficiency ratio separates structural constraints from allocation failures
- "So what if the distribution is off?" → design effect shows the precision cost
- "Why not just reweight?" → reweighting fixes bias but effective N shows the precision you can't recover

### 8. What This Does NOT Require

- **No new divergence measure.** The GRI stays TVD-based. The design effect is a standard derived quantity, not a competing metric.
- **No opinion/response data.** All metrics derive from sample proportions and population benchmarks alone.
- **No changes to the GRI's mathematical properties or proofs.**
- **No changes to the Diversity Score, SRI, or Monte Carlo maximum framework.**
- **No renaming.** "Global Representativeness Index" accurately describes what the metric computes. The paper's narrative — not the name — carries the "why this matters" argument.
