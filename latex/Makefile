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

.PHONY: all figures paper clean arxiv

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

# Create arXiv-ready archive
arxiv: paper
	tar -czf gri-whitepaper-arxiv.tar.gz \
		$(MAIN).tex \
		$(MAIN).bbl \
		references.bib \
		$(FIGDIR)/*.pdf \
		$(FIGDIR)/generate_figures.py
	@echo "Created: gri-whitepaper-arxiv.tar.gz"
	@echo "Upload this file to arXiv."
