# GRI Whitepaper — LaTeX Build

## Prerequisites

- Python 3.8+ with `pandas`, `numpy`, `matplotlib`
- pdflatex and bibtex (TeX Live or similar)

## Building

```bash
# Generate figures from repository data
make figures

# Compile the paper
make paper

# Create arXiv-ready archive
make arxiv

# Clean build artifacts
make clean
```

## Files

- `main.tex` — Full paper source
- `references.bib` — Bibliography entries
- `figures/generate_figures.py` — Script to produce figures from repo data
- `figures/*.pdf` — Generated figures (after running `make figures`)
- `Makefile` — Build automation

## Notes

- Figures are generated from `analysis_output/scorecards/GD_combined_scorecards.csv` in the parent repository
- Citations marked as commented-out in `references.bib` need verification before final submission
- Run `make figures` before `make paper` to ensure all figure files exist
