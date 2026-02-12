# GRI Whitepaper: Expert Reviews

---

## Review 1: Senior Survey Statistician

**Reviewer expertise**: Sampling theory, post-stratification, design-based inference, R-indicators, calibration estimation. 20+ years in national statistical offices and survey methodology research.

### Summary

This paper proposes the Global Representativeness Index (GRI), a metric based on Total Variation Distance for measuring how well a survey sample's demographic composition matches a target population. The authors apply the framework to six waves of the Global Dialogues survey, introduce two metric variants (SRI, VWRS), and release an open-source Python library. The core idea is sound and fills a genuine gap, but several methodological issues require attention before the paper is suitable for publication.

### Major Issues

**1. The GRI conflates sampling quality with sampling design, obscuring its inferential implications.**

The paper states that the GRI measures "distributional fidelity" but does not adequately address how it relates to the bias of survey estimates. A sample can have low GRI (poor demographic match) yet produce unbiased estimates of population means if appropriate weights are applied. Conversely, a sample with high GRI can still produce biased estimates if the sample is non-random within strata (e.g., all respondents are highly educated urbanites within each country-gender-age cell). The paper should be explicit that GRI measures *marginal distributional distance*, not inferential quality, and discuss the conditions under which marginal balance implies reduced estimation bias.

**2. The choice of TVD over alternatives is inadequately justified.**

Section 2.3 dismisses KL divergence, Hellinger distance, and chi-squared distance with brief arguments. The claim that TVD is more "interpretable" than Hellinger is subjective. More critically, the paper does not discuss that TVD is *the least sensitive* of these metrics to small-probability events — a Hellinger-based index would penalize missing rare strata more than TVD does. Given that the paper separately introduces a Diversity Score to capture rare-stratum coverage (which TVD handles poorly), this suggests TVD alone is insufficient. Why not use Hellinger distance and eliminate the need for a separate Diversity Score? The paper should either provide a formal argument for the TVD + Diversity Score combination or consider alternative base metrics.

**3. The Monte Carlo "maximum achievable GRI" conflates two distinct constraints.**

The maximum GRI simulation assumes optimal allocation subject to integer constraints. But the actual constraint on real surveys is not integer rounding — it is the *availability of respondents* in each stratum. The paper should distinguish between: (a) the allocation-constrained maximum (what you compute), (b) the coverage-constrained maximum (which depends on the sampling frame's coverage of strata), and (c) the design-constrained maximum (which depends on the sampling mechanism). The current simulation answers "what if we had an oracle allocator?" but real surveys face recruitment friction that makes even the integer-constrained optimum unachievable.

**4. The VWRS formulation has a technical problem with the weight definition.**

The weight $w_i = q_i \cdot \text{SE}_i \cdot r_i$ uses the standard error $\text{SE}_i = \sqrt{\hat{p}_i(1-\hat{p}_i)/n_i}$, where $\hat{p}_i$ is described as an "opinion proportion within stratum $i$." But the VWRS is presented as a *representativeness* metric, not an opinion-estimation metric. The standard error of an opinion proportion within a stratum is irrelevant to whether that stratum is proportionally represented. The paper conflates two goals: measuring distributional match (GRI's purpose) and measuring estimation reliability (a design-based inference question). The weight should be justified on representativeness grounds, not opinion-estimation grounds, or the VWRS should be explicitly framed as a hybrid metric.

**5. Treatment of R-indicators is incomplete and somewhat unfair.**

The paper states that R-indicators "require auxiliary data about nonrespondents" (Section 2.2). This is not quite right — R-indicators require auxiliary data about the *target population*, which is used to model response propensities. This is conceptually similar to the GRI's requirement for population benchmarks. The paper should provide a more careful comparison, noting that R-indicators and GRI answer different questions (response propensity variation vs. achieved distributional distance) rather than presenting R-indicators as simply inferior due to data requirements.

### Minor Issues

- The interpretation scale (Table in Section 3.1.3) lacks empirical or theoretical justification for the specific thresholds. Why 0.4 and 0.6? Are these based on the TVD literature, simulation studies, or expert consensus?
- The paper claims "no global survey achieves high GRI on fine-grained dimensions at moderate sample sizes" (Section 5.1) but provides no evidence beyond the Global Dialogues. Has the framework been applied to WVS or Gallup World Poll data for comparison?
- The term "demographic weight" in "69% of the sample's demographic weight is misallocated" is imprecise. TVD measures probability mass misallocation; "demographic weight" could be misread as survey weights.
- In Appendix A.2, the monotonicity proof assumes $\delta \leq \min(p_j - q_j, q_k - p_k)$, which ensures the signs don't flip. The general case (where reallocation crosses the target) is more complex and should be noted.
- The Diversity Score threshold discussion should cite the Poisson approximation explicitly and note its limitations for large $q_i$.
- Table 1 reports means and standard deviations across 6 waves, but with only 6 data points these statistics are not very informative. Consider just reporting the range.

### Questions for the Authors

1. Have you computed GRI for any probability-based survey (e.g., WVS, ESS) to provide a reference point for what "typical" GRI scores look like when sampling is designed for representativeness?
2. How does the GRI handle survey design weights? If a survey uses post-stratification to correct its demographic profile, should the GRI be computed on the weighted or unweighted sample?
3. The SRI's square-root target lacks theoretical motivation beyond "it boosts small strata." Is there a formal optimality result justifying $\sqrt{q_i}$ specifically (as opposed to, say, $q_i^{2/3}$ or the Neyman allocation target)?

### Recommendation

**Major revision.** The core contribution — a standardized, reproducible metric for sample representativeness — is valuable and timely. However, the relationship between GRI and inferential bias needs clarification, the metric choice requires stronger justification, and the VWRS formulation has a conceptual problem. With revisions addressing these issues, the paper would make a solid contribution to survey methodology.

---

## Review 2: Global Development / Political Science Researcher

**Reviewer expertise**: Large-scale multi-country surveys for policy research (World Values Survey, Afrobarometer, UNDP Human Development Report surveys). 15 years designing and analyzing cross-national survey instruments.

### Summary

This paper introduces a quantitative metric for measuring survey representativeness against global population benchmarks and demonstrates it on the Global Dialogues AI perception survey. The framework is well-implemented and practically useful. My concerns relate primarily to the "global" framing, the benchmark data choices, and whether the case study adequately demonstrates the method's value.

### Major Issues

**1. The "global" frame is undertheorized and politically loaded.**

The paper assumes that the relevant population for representativeness is the *entire world*, with each person weighted equally regardless of political jurisdiction, institutional context, or relevance to the research question. This is a strong normative claim that the paper does not defend. For AI governance research specifically, one could argue that representativeness should be weighted by a country's AI capability, regulatory influence, or affected-population size — not raw headcount. China's 18% population share does not necessarily mean Chinese respondents should constitute 18% of an AI governance survey sample; it depends on what the survey aims to inform.

The paper should acknowledge that "global representativeness" is not a neutral statistical concept but a choice about whose voices count equally. The GRI as formulated embeds a specific normative position: *one person, one unit of representativeness*. This position is defensible but should be made explicit and discussed, not assumed.

**2. The 2010 religious benchmark is indefensible for a 2024 publication.**

The Pew Global Religious Landscape data dates to 2010. In 14 years, religious demographics have shifted meaningfully in several regions: China's religious revival (or state suppression, depending on the measure), rapid secularization in Western Europe and East Asia, growth of "spiritual but not religious" identities, and the rise of Pentecostalism in Sub-Saharan Africa and Latin America. Using 2010 data means the GRI's religious dimension measures distance from a *historical* population, not the current one. Pew published updated projections in 2015 and 2020. Why not use those? If disaggregated data isn't available, the limitation should be discussed much more prominently — not buried in Section 7.1 as a brief paragraph.

**3. Why only these three dimensions?**

The paper evaluates Country × Gender × Age, Country × Religion, and Country × Environment. But many dimensions critical to representativeness are missing: education level, income/socioeconomic status, language, disability status, indigenous/minority status, internet access. The paper's choice to include religion but not education seems arbitrary. Education is arguably more consequential for opinion formation than religion, and UNESCO provides country-level education statistics that could serve as benchmarks. The rationale for including these three dimensions and not others should be explicitly argued, not just stated.

**4. The case study demonstrates the metric but not its value.**

The paper applies GRI to six waves of the Global Dialogues survey and finds low scores. But so what? The paper does not show that the low GRI scores correspond to biased findings — that the AI perception results would be meaningfully different with a more representative sample. Without this connection, the GRI remains an interesting metric in search of demonstrated consequences. Even a brief analysis showing, for example, that response patterns differ between high-GRI and low-GRI demographic segments would substantially strengthen the empirical contribution.

**5. The framework doesn't address what practitioners need most: subnational variation.**

Most survey practitioners worry about representativeness *within* their country, not across the globe. A nationally representative sample of 1,000 Nigerians that oversamples Lagos and Abuja at the expense of rural northern Nigeria has a major representativeness problem that the GRI (as currently defined against global benchmarks) would not capture. The paper frames this as a feature ("any categorical demographic variable with a population benchmark can be added"), but in practice the library ships only with global benchmarks. To be useful beyond the niche of global surveys, the framework needs subnational benchmark integration — or the paper should more honestly scope its contribution to global-level measurement.

### Minor Issues

- The efficiency ratio is a useful concept but the name is potentially confusing — in survey statistics, "efficiency" typically refers to the ratio of variances under different estimation procedures.
- The paper's claim that "even well-designed global surveys achieve GRI scores of only 0.29–0.37" generalizes from one survey (Global Dialogues, which uses convenience sampling) to all global surveys. This is an overstatement.
- Table 4 (metric variant comparison) uses GD5 only. A comparison across all waves would be more convincing.
- The "Best Practices" section (6.3) reads more like API documentation than methodological guidance. What are the actual best practices for *designing* a survey with GRI targets? How should a researcher balance GRI across dimensions? What's the minimum sample size for meaningful GRI analysis?
- The paper does not discuss ethical considerations. If GRI targets drive sampling, they could incentivize surveying hard-to-reach populations without adequate ethical oversight (e.g., surveying rural populations in conflict zones to boost representation).

### Questions for the Authors

1. Has the GRI been applied to the World Values Survey or another probability-based global survey for comparison?
2. Would you consider a weighted version of the GRI where dimension weights reflect the research context (e.g., for health research, weight age and gender higher; for governance research, weight country higher)?
3. How do you recommend practitioners handle the tension between GRI optimization and survey budget constraints? Recruiting in underrepresented countries (e.g., Chad, Myanmar) is dramatically more expensive than in well-connected countries.

### Recommendation

**Major revision.** The metric itself is well-designed, the implementation is solid, and the paper is well-written. But the framing needs to be more honest about the normative choices embedded in "global representativeness," the benchmark data limitations need more prominent treatment, the case study needs to demonstrate *consequences* of low representativeness (not just the fact), and the practical utility for non-global surveys should be addressed.

---

## Review 3: Machine Learning / AI Safety Researcher

**Reviewer expertise**: Dataset representativeness for ML training data and evaluation benchmarks, fairness in AI systems, distribution shift, dataset documentation practices. Published on Datasheets for Datasets and algorithmic auditing.

### Summary

The GRI paper proposes a TVD-based framework for quantifying survey representativeness and applies it to AI perception surveys. As someone working on dataset quality for ML systems, I see clear parallels between this work and the dataset documentation and representativeness assessment problems in my field. The framework is rigorous and the implementation is mature. My main concerns are about scalability, connections to the ML fairness literature, and the Diversity Score's threshold choice.

### Major Issues

**1. The connection to ML dataset representativeness is undersold.**

The paper motivates itself primarily through survey methodology, but the GRI framework is directly applicable to ML dataset auditing — a rapidly growing concern in AI safety. Training datasets like LAION-5B, Common Crawl, and The Pile have known demographic skews that affect model behavior. Evaluation benchmarks (MMLU, BigBench, HELM) face similar representativeness questions. The GRI could provide a standardized metric for reporting demographic composition of these datasets, analogous to what Datasheets for Datasets [Gebru et al., 2021] advocates qualitatively. The paper mentions AI governance in the introduction but never develops this connection. A subsection on ML dataset applications — including a discussion of how the GRI relates to distribution shift metrics in the ML literature — would substantially broaden the paper's audience and impact.

**2. Scalability concerns for high-dimensional demographic spaces.**

The paper acknowledges in Section 7.7 that adding dimensions multiplicatively increases strata, but dismisses this by noting that the scorecard evaluates pairs of crossed dimensions separately. This is a significant limitation. In ML fairness, we often care about *intersectional* representativeness — the joint distribution across race, gender, age, disability, and other protected attributes simultaneously. With 5 dimensions of 5 categories each, we'd have $5^5 = 3,125$ strata. At 10 dimensions of 5 categories, we'd have nearly 10 million. The paper should discuss: (a) whether the pairwise scorecard approach loses important information about higher-order interactions, and (b) whether approximation methods (e.g., random projection, hashing) could extend the framework to higher-dimensional spaces.

**3. The Diversity Score threshold $X = 1/N$ is principled but its implications are underexplored.**

The $1/N$ threshold has a clean interpretation (expected count ≥ 1) but creates a moving target. As $N$ increases, more strata become "relevant" and the Diversity Score can *decrease* even as the sample grows, because new strata are added to the denominator faster than they're covered. This non-monotonicity in $N$ should be discussed and illustrated. It means the Diversity Score is not a simple "bigger sample → better score" metric, which could confuse practitioners.

Additionally, for ML datasets with millions of items, $1/N$ becomes vanishingly small, making virtually all strata "relevant" and reducing the Diversity Score to a simple coverage count. The threshold's behavior at different scales should be analyzed.

**4. No connection to fairness metrics or distribution shift literature.**

The ML fairness community has developed extensive metrics for assessing distributional distance between datasets: demographic parity distance, equalized odds gap, calibration differences. The distribution shift literature uses metrics like Maximum Mean Discrepancy (MMD), Wasserstein distance, and domain divergence bounds. The paper should position the GRI within this landscape. Specifically:

- How does GRI relate to demographic parity? (GRI measures population-proportional representation, which is essentially demographic parity of *sampling probability*.)
- How does TVD compare to MMD for this use case? (MMD works in continuous spaces; TVD requires discretization. This is a meaningful tradeoff.)
- The paper's "efficiency ratio" concept resembles the concept of "optimal transport cost" — is there a formal connection?

**5. Benchmark uncertainty propagation is absent.**

The paper treats population benchmarks as known quantities, but they're estimates. For ML applications, the "population" may itself be uncertain (what's the "true" distribution of concepts in the real world?). A Bayesian treatment that propagates benchmark uncertainty into GRI confidence intervals — even approximate — would make the framework more robust and honest. At minimum, the paper should discuss sensitivity of GRI scores to benchmark perturbations.

### Minor Issues

- The code examples in Section 6.2 are useful but should include error handling and edge cases (empty strata, missing categories) to be realistic.
- The paper doesn't discuss computational complexity. For large datasets and many strata, what's the time/space complexity of GRI computation? This matters for real-time monitoring (Section 6.3) of large-scale data collection.
- The SRI's $\sqrt{q_i}$ target is reminiscent of the "square root law" in sampling theory and also appears in information-theoretic optimal quantization. This connection should be cited.
- The VWRS's use of opinion-response variance to weight strata conflates representativeness measurement with outcome measurement. A representativeness metric should depend only on the demographic composition, not on what questions are being asked.
- The Monte Carlo simulation for maximum GRI uses 1,000 iterations. Has convergence been verified? What's the standard error of the mean max GRI estimate?

### Questions for the Authors

1. Have you considered applying the GRI to ML training or evaluation datasets? What modifications would be needed?
2. Could the GRI framework be extended to continuous demographics using kernel density estimation or quantile-based discretization?
3. How does the framework handle intersectional analysis — e.g., ensuring that *women of color in rural areas* are represented, not just that women, people of color, and rural residents are each separately well-represented?
4. What is the computational cost of the scorecard generation (all 13 dimensions) for a typical dataset? Does it scale linearly in sample size?

### Recommendation

**Accept with major revisions.** The core contribution is strong: a well-defined, interpretable, and implemented metric for distributional representativeness. The framework fills a real need in both survey methodology and ML dataset quality assessment. The main gaps are: (1) inadequate connection to ML/AI fairness literature, (2) unaddressed scalability for high-dimensional intersections, (3) missing analysis of Diversity Score non-monotonicity, and (4) absent benchmark uncertainty treatment. These are addressable through additional discussion and modest extensions, not fundamental rethinking.

---

## Author Responses

### Responses to Reviewer 1 (Survey Statistician)

**Major Issue 1 — GRI conflates sampling quality with inferential quality.** We agree this was under-discussed. We added Section 1.4 ("Scope and Normative Commitments") explicitly stating that the GRI measures *marginal distributional distance*, not inferential quality, and clarifying the conditions under which distributional match reduces (but does not eliminate) the need for post-stratification weights and the model assumptions they require.

**Major Issue 2 — TVD choice needs stronger justification.** We substantially expanded Section 2.3 with a direct comparison of TVD + Diversity Score vs. a Hellinger-based approach. We argue for TVD on three grounds: (1) interpretability ("fraction of mass misallocated"), (2) additive decomposability for segment-level diagnostics, and (3) separation of concerns between distributional fidelity and coverage. We also added the formal relationship between TVD and Hellinger to show they are never wildly discrepant.

**Major Issue 3 — Monte Carlo max conflates constraints.** We added a caveat paragraph in Section 3.4 explicitly distinguishing the allocation-constrained maximum (what we compute) from the coverage-constrained and design-constrained maxima that real surveys face. We now describe the max GRI as an "upper bound on the upper bound."

**Major Issue 4 — VWRS weight conflates representativeness with opinion estimation.** Upon further analysis, we agree with this critique. The VWRS has been removed from the paper entirely. The question it attempted to answer — "how consequential are distributional gaps for inference?" — is now addressed through the design effect framework (new Section 3.6), which connects distributional mismatch to variance inflation using established survey statistics rather than an ad hoc weighting scheme. The efficiency ratio (GRI / Max GRI) addresses the separate concern that raw GRI scores seem "too harsh" at moderate sample sizes.

**Major Issue 5 — R-indicator treatment is incomplete.** We revised both Section 1.2 and Section 2.2 to provide a more careful comparison, noting that R-indicators and GRI both require population data but answer different questions (response mechanism variation vs. achieved distributional distance), and that R-indicators are well-suited to probability samples while GRI applies to both probability and non-probability designs.

**Minor issues:** Interpretation scale now cites calibration against Monte Carlo simulations. Monotonicity proof now notes the general case where overshooting is possible. We replaced "demographic weight" with "probability mass" where precision is needed. We use range rather than SD for the 6-wave summary where appropriate.

**Questions:** (1) We have not yet applied GRI to WVS — this is noted as important future validation. (2) The GRI applies to the unweighted sample; evaluating post-stratified samples is noted as future work. (3) We added formal motivation for the SRI's √q target, connecting it to minimax relative estimation error under proportional heterogeneity.

### Responses to Reviewer 2 (Political Science)

**Major Issue 1 — "Global" framing is undertheorized.** We added Section 1.4 explicitly acknowledging that "one person, one unit of representativeness" is a normative choice, not a neutral statistical default. We discuss alternative weighting schemes (by AI capability, regulatory influence, etc.) and note that the framework accommodates custom benchmarks.

**Major Issue 2 — 2010 religious benchmark.** We substantially expanded Section 7.1 with a frank discussion of why the 2010 data is used (most comprehensive observed cross-national religious data; 2015 projections are model-based and not available in disaggregated form), while acknowledging this is unsatisfying. We added specific recommendations: report benchmark vintage, update on 5-year cycles, and conduct sensitivity analysis.

**Major Issue 3 — Why these three dimensions?** We added explicit selection criteria in Section 3.3.1: availability of authoritative global data, established relevance in social science, and respondent observability. We acknowledge that education, income, and other dimensions are arguably equally important but lack globally comparable country-level distributions.

**Major Issue 4 — Case study doesn't show consequences.** We acknowledge this gap. A full analysis of whether low-GRI segments produce systematically different response patterns would require analysis of the survey content variables, which is outside the scope of this methodological paper. We note this as important future work in the discussion section. The segment-level decomposition (Section 4.5) does demonstrate the *diagnostic* value of the framework.

**Major Issue 5 — Subnational variation.** We added Section 7.8 addressing this directly, noting that the framework is technically applicable at any geographic scope with appropriate benchmarks, but the current library ships only with global benchmarks. Subnational benchmark integration is identified as a development priority.

**Minor issues:** Removed overgeneralizations ("even well-designed global surveys" → "this purposive online survey"). Expanded best practices discussion.

### Responses to Reviewer 3 (ML/AI Safety)

**Major Issue 1 — ML dataset connection undersold.** We added Section 5.4 ("Beyond Surveys: Applications to Machine Learning Dataset Auditing") discussing the framework's applicability to ML training data and evaluation benchmarks, connections to Datasheets for Datasets and fairness metrics, and the relationship between GRI and demographic parity of sampling probability.

**Major Issue 2 — Scalability concerns.** We expanded Section 7.7 to discuss the curse of dimensionality in intersectional representativeness, the limitations of the pairwise scorecard approach for capturing higher-order interactions, and potential extension paths (random projections, parametric approaches).

**Major Issue 3 — Diversity Score non-monotonicity.** We added detailed discussion in Section 7.5 documenting this property, explaining why it is semantically correct (larger samples should be held to higher coverage standards), and noting implications for cross-sample comparison and ML datasets with large N.

**Major Issue 4 — Fairness metrics connection.** Addressed in new Section 5.4. We explicitly connect GRI to demographic parity, compare TVD with MMD, and note the relationship between the efficiency ratio and optimal transport concepts.

**Major Issue 5 — Benchmark uncertainty.** Section 7.6 already discussed this; we note that a fully Bayesian treatment remains future work. The sensitivity analysis recommendation in the expanded Section 7.1 provides a practical interim approach.

**Minor issues:** Added note on Monte Carlo convergence (1,000 simulations with SDs in the 0.003–0.017 range, indicating well-converged estimates). Added new Section 3.6 on the inferential cost of low representativeness, connecting GRI to design effect and effective sample size.
