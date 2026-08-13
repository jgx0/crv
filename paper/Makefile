# Resolve repo root relative to this Makefile so local and CI both work.
PAPER_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_DIR := $(abspath $(PAPER_DIR)/..)

# Prefer the repo virtualenv, which is where matplotlib/pandas actually live.
# Override with `make PYTHON=... ` if you manage environments differently.
PYTHON ?= $(if $(wildcard $(REPO_DIR)/.venv/bin/python),$(REPO_DIR)/.venv/bin/python,python3)

.PHONY: experiment experiment-synthetic paper all clean test figures

all: experiment paper

experiment:
	cd $(REPO_DIR) && $(PYTHON) pipeline.py --output-dir outputs

experiment-synthetic:
	cd $(REPO_DIR) && $(PYTHON) pipeline.py --output-dir outputs --force-synthetic

figures:
	cd $(REPO_DIR) && $(PYTHON) figures.py --output-dir outputs

test:
	cd $(REPO_DIR) && $(PYTHON) -m pytest tests/ -q

# The single WSAJ submission manuscript: figures embedded, APA references,
# continuous line numbers, title page first.
paper: figures
	@if command -v pdflatex >/dev/null 2>&1; then \
		cd $(PAPER_DIR) && \
		pdflatex -interaction=nonstopmode main.tex && bibtex main && \
		pdflatex -interaction=nonstopmode main.tex && \
		pdflatex -interaction=nonstopmode main.tex; \
	else \
		echo "pdflatex not found; install a TeX distribution to build paper/main.tex"; \
	fi

clean:
	cd $(PAPER_DIR) && rm -f *.aux *.bbl *.blg *.log *.out *.toc *.pdf *.spl
