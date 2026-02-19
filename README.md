# Global Representativeness Index (GRI)

A framework for measuring how well survey samples represent their target population across demographic dimensions. The GRI uses Total Variation Distance to produce interpretable scores on a [0, 1] scale, where 1 indicates a perfect demographic mirror and values below 0.4 signal serious distributional mismatch.

**Paper:** [arXiv:2602.14835](https://arxiv.org/abs/2602.14835)
**Website:** [gri.cip.org](https://collect-intel.github.io/gri/)
**Citation:** See [below](#citation)

## Quick Start

```bash
pip install -e .
```

```python
from gri import calculate_gri, load_benchmark_suite

benchmarks = load_benchmark_suite()
gri_score = calculate_gri(
    survey_df, benchmarks['country_gender_age'],
    strata_cols=['country', 'gender', 'age_group']
)
```

## Reproducibility

**Setup** (one-time):

```bash
git clone --recurse-submodules https://github.com/collect-intel/gri.git
cd gri
make setup           # creates venv, installs deps, processes benchmark data
```

**Reproduce all paper artifacts:**

```bash
make reproduce       # GD scorecards → combined CSV → figures (PDF + PNG) → max scores
make test            # 271 tests including property-based mathematical invariants
```

`make reproduce` generates:
- Individual + combined scorecards in `analysis_output/scorecards/`
- Paper figures (PDF) in `latex/figures/`
- Site images (PNG) in `site/images/`
- Monte Carlo maximum achievable GRI scores in `analysis_output/`

**Additional targets** (require external data due to license restrictions):

```bash
make scorecards-wvs       # World Values Survey (download from worldvaluessurvey.org)
make scorecards-regional  # Afrobarometer + Latinobarómetro
make site-figures         # comparison figures across all 5 surveys
```

Run `make help` for the full list of available targets.

The Global Dialogues survey data is included via git submodule. WVS and regional survey data (Afrobarometer, Latinobarómetro, Pew) require separate download due to license restrictions — see `data/raw/survey_data/` for details.

## Project Structure

```
gri/                  Python library (calculator, scorecard, design effect, SRI, ...)
scripts/              Data processing and scorecard generation
latex/                Paper source (canonical), figures, Makefile
data/raw/             Benchmark data (UN, Pew) + survey data (git submodule)
analysis_output/      Generated scorecards and results
tests/                Test suite (pytest)
config/               YAML configuration for dimensions and segments
```

## Key Metrics

| Metric | What It Measures |
|--------|-----------------|
| **GRI** | Distributional fidelity (1 - TVD from target) |
| **Diversity Score** | Strata coverage fraction |
| **Design Effect** | Variance inflation from post-stratification reweighting |
| **Effective N** | N / d_eff — usable sample size for inference |
| **SRI** | Match to strategically optimal (sqrt-proportional) allocation |
| **Efficiency Ratio** | Actual GRI / Monte Carlo maximum GRI |

## Citation

```bibtex
@article{hadfield2025gri,
  title  = {The Global Representativeness Index: Measuring Demographic
            Representativeness in Survey Samples Using Total Variation Distance},
  author = {Hadfield, Evan and Konya, Andrew},
  year   = {2025},
  eprint = {2602.14835},
  archivePrefix = {arXiv},
  url    = {https://arxiv.org/abs/2602.14835}
}
```

## License

MIT
