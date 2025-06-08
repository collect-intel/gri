# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the **Global Representativeness Index (GRI)** project - a research tool for measuring how well survey samples represent the global population across demographic dimensions. The project has two main components:

1. **GRI Core Library** (planned) - Python library for calculating representativeness scores using Total Variation Distance
2. **Global Dialogues Analysis** (existing) - Complete data analysis pipeline for AI perception surveys

## Architecture

The codebase follows a research data analysis structure:

```
/gri (planned core library)
/data/raw/benchmark_data/ (UN & Pew demographic benchmarks)
/data/raw/survey_data/global-dialogues/ (Git submodule with analysis tools)
/scripts/ (planned GRI data processing)
/notebooks/ (planned GRI examples)
```

The Global Dialogues component is a Git submodule with its own complete analysis pipeline and Makefile.

## Common Development Commands

### Global Dialogues Analysis (Current)
```bash
# Navigate to the submodule
cd data/raw/survey_data/global-dialogues

# Install dependencies
pip install -r requirements.txt

# See all available commands
make help

# Typical workflow for analyzing GD3 data
make preprocess GD=3
make analyze GD=3
make download-embeddings GD=3

# Individual analysis components
make consensus GD=3
make divergence GD=3
make indicators GD=3
make pri GD=3
```

### GRI Core Library (Planned)
```bash
# Process benchmark demographic data
python scripts/process_data.py

# Run core GRI calculations (when implemented)
python -c "from gri import calculate_gri; ..."

# Run example notebooks
jupyter notebook notebooks/2-gri-calculation-example.ipynb

# Run tests
pytest tests/
```

## Key Data Sources

**Benchmark Data** (`data/raw/benchmark_data/`):
- `WPP_2023_Female_Population.csv` / `WPP_2023_Male_Population.csv` - UN population by country/age/gender
- `GLS_2010_Religious_Composition.csv` - Pew religious demographics by country  
- `WUP_2018_Urban_Rural.csv` - UN urban/rural distribution by country
- `Sources.csv` - Full attribution for all data sources

**Survey Data** (Git submodule):
- Processed files: `GD<N>_aggregate_standardized.csv` (use this for analysis)
- Raw exports: `GD<N>_aggregate.csv`, `GD<N>_participants.csv`, etc.
- Analysis outputs: `analysis_output/GD<N>/` directories

## Core Concepts

**GRI Calculation**: `GRI = 1 - (0.5 * Σ|sample_proportion - population_proportion|)`
- Measures how closely sample demographics match global population
- Score ranges 0.0 (complete mismatch) to 1.0 (perfect match)
- Applied across multiple dimensions: Country×Gender×Age, Country×Religion, Country×Environment

**Global Dialogues Analysis**:
- **Consensus**: Responses with broad demographic agreement
- **Divergence**: Responses that polarize across demographics  
- **PRI (Participant Reliability Index)**: Quality scoring for participants
- **Indicators**: Thematic tracking of AI perception over time

## Development Patterns

1. **Use the Makefile**: The Global Dialogues component has comprehensive Make commands for all operations
2. **Follow the PROJECT_PLAN.md**: Detailed implementation guide for the GRI core library
3. **Data file naming**: Always use `GD<N>_aggregate_standardized.csv` for analysis (not raw exports)
4. **Modularity**: Both components demonstrate good separation between data processing, analysis, and output generation

## Environment Setup

- Python dependencies in `requirements.txt` (Global Dialogues) 
- Optional API keys in `.env`: `OPENAI_API_KEY`, `OPENROUTER_API_KEY` (for LLM-based analysis)
- Large embedding files downloaded separately (not in Git): `GD<N>_embeddings.json`

## Testing and Quality

- Global Dialogues: Use `make preprocess GD=<N>` before analysis to ensure clean data
- GRI Core: Planned unit tests in `tests/` directory using pytest
- Data validation: Scripts include error handling for missing/malformed data