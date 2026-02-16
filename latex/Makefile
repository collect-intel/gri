# Makefile for GRI Whitepaper LaTeX build
#
# Usage:
#   make figures  - Generate figures from data
#   make paper    - Compile LaTeX to PDF
#   make clean    - Remove build artifacts
#   make arxiv    - Create arXiv-ready archive

MAIN = main
FIGDIR = figures
FIGSCRIPT = $(FIGDIR)/generate_figures.py

.PHONY: all figures paper clean reproduce

all: figures paper

# Generate figures from repository data
figures:
	cd $(FIGDIR) && python generate_figures.py

# Compile LaTeX (pdflatex + bibtex + 2x pdflatex for references)
paper: $(MAIN).tex references.bib
	pdflatex $(MAIN)
	bibtex $(MAIN)
	pdflatex $(MAIN)
	pdflatex $(MAIN)

# Clean build artifacts
clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out
	rm -f $(MAIN).toc $(MAIN).lof $(MAIN).lot $(MAIN).fls $(MAIN).fdb_latexmk
	rm -f $(MAIN).synctex.gz

# Regenerate all data then build paper
reproduce:
	cd .. && make reproduce
	$(MAKE) figures

# arXiv archive: use `make arxiv` from project root
