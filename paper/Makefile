PYTHON ?= python
PAPER_DIR := /home/runner/work/crv/crv/paper
REPO_DIR := /home/runner/work/crv/crv

.PHONY: experiment paper all clean

all: experiment paper

experiment:
	cd $(REPO_DIR) && $(PYTHON) pipeline.py --output-dir outputs

paper:
	@if command -v pdflatex >/dev/null 2>&1; then \
		cd $(PAPER_DIR) && pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex; \
	else \
		echo "pdflatex not found; install a TeX distribution to build paper/main.tex"; \
	fi

clean:
	cd $(PAPER_DIR) && rm -f *.aux *.bbl *.blg *.log *.out *.toc *.pdf
