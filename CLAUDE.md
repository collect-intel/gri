# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **Global Representativeness Index (GRI)** — a framework for measuring how well survey samples represent their target population across demographic dimensions, using Total Variation Distance.

- **Paper**: `latex/main.tex` (canonical; archived Markdown draft in `drafts/`)
- **Library**: `gri/` Python package (16 modules)
- **Website**: https://collect-intel.github.io/gri/

## Architecture

```
gri/                  Core library (calculator, scorecard, design_effect, strategic_index, ...)
scripts/              Data processing and scorecard generation
latex/                Paper source, figures, Makefile
data/raw/             Benchmark data (UN, Pew) + survey data (git submodule)
analysis_output/      Generated scorecards and results
tests/                pytest suite
config/               YAML configuration (dimensions.yaml, segments.yaml)
```

## Common Commands

```bash
# Reproducibility
make reproduce          # Regenerate GD scorecards + figures
make scorecards-wvs     # WVS scorecards (requires external data)
make scorecards-regional # Regional scorecards (requires external data)

# Development
make test               # Run test suite
make setup              # Full setup (venv + install + data)
make scorecard GD=3     # Single GD scorecard

# Data processing
python scripts/process_data.py
python scripts/generate_gd_scorecards.py
python scripts/generate_wvs_scorecards.py
python scripts/generate_regional_scorecards.py
```

## Key Data Sources

**Benchmark Data** (`data/raw/benchmark_data/`):
- `WPP_2023_Female_Population.csv` / `WPP_2023_Male_Population.csv` — UN population by country/age/gender
- `GLS_2010_Religious_Composition.csv` — Pew religious demographics by country
- `WUP_2018_Urban_Rural.csv` — UN urban/rural distribution by country

**Survey Data** (via git submodule):
- `data/raw/survey_data/global-dialogues/` — Global Dialogues GD1-GD8
- WVS, Afrobarometer, Latinobarómetro data requires separate download (license restrictions)

## Core Concepts

**GRI**: `1 - TVD(sample, population)` — score from 0 (disjoint) to 1 (perfect match)
**Diversity Score**: fraction of relevant strata (q_i > 1/N) that are represented
**Design Effect**: `Σ(q_i²/p_i)` — variance inflation from post-stratification reweighting
**SRI**: GRI variant using sqrt-proportional targets for survey design
**Efficiency Ratio**: actual GRI / Monte Carlo maximum GRI

## Development Patterns

- `config/segments.yaml` is the single source of truth for country name standardization
- `GRIScorecard` is the high-level class for multi-dimensional scorecard generation
- Scripts use `sys.path.insert(0, ...)` to load the local dev version of `gri/`
- Data file naming: use `GD<N>_participants.csv` via the git submodule

## Testing

```bash
make test               # Run all tests
pytest tests/ -v        # Verbose output
pytest tests/test_properties.py  # Property-based invariant tests
pytest tests/test_design_effect.py  # Design effect unit tests
```
