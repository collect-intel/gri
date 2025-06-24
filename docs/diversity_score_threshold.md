# Diversity Score Threshold Documentation

## Overview

The diversity score uses a threshold of X = 1/N (where N is the sample size) to determine which strata are "relevant" for coverage calculation. This threshold represents an expected count of 1 participant per stratum.

## Why 1/N instead of 1/(2N)?

### The Original Approach (1/2N)

Initially, the GRI diversity score used X = 1/(2N) based on the logic that:
- It represents an expected count of 0.5 participants
- This rounds up to 1 participant in practice
- It allows counting smaller strata as "relevant"

### The Problem

Analysis revealed that 1/(2N) systematically overcounts achievable diversity:

1. **Low probability of observation**: A stratum with expected count 0.5 has only ~39% probability of appearing in the sample (based on Poisson distribution: 1 - e^(-0.5) ≈ 0.393)

2. **Cumulative overestimation**: With many small strata near the threshold, the diversity score counts many strata that won't actually appear, inflating the denominator

3. **Unrealistic expectations**: Simulations show 1/(2N) overestimates achievable diversity by 30-60% compared to actual sampling outcomes

### The Better Approach (1/N)

Using X = 1/N provides:

1. **Higher observation probability**: ~63% chance of observing at least one participant (1 - e^(-1) ≈ 0.632)

2. **Cleaner interpretation**: "Strata where we expect at least 1 participant"

3. **More accurate assessment**: Better alignment between theoretical expectations and actual achievable diversity

4. **Realistic benchmarks**: Diversity scores that reflect what can actually be achieved in practice

## Impact of the Change

For typical surveys:
- Diversity scores decrease by 2-5%
- The number of "relevant" strata decreases (higher threshold)
- The percentage of covered relevant strata may increase or decrease depending on the distribution

Example for GD3 (n=986):
- Old threshold (1/2N): 0.00051 (0.051% of world population)
- New threshold (1/N): 0.00101 (0.101% of world population)
- Diversity score change: 0.8438 → 0.8276

## Alternative Thresholds

Other reasonable choices include:
- **2/N**: Very conservative (86% observation probability)
- **1.5/N**: Middle ground (78% observation probability)
- **Custom threshold**: Based on specific research needs

The 1/N threshold balances statistical rigor with practical interpretation.