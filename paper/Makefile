# Resolve repo root relative to this Makefile so local and CI both work.
PAPER_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_DIR := $(abspath $(PAPER_DIR)/..)

# Prefer the repo virtualenv, which is where matplotlib/pandas actually live.
# Override with `make PYTHON=... ` if you manage environments differently.
PYTHON ?= $(if $(wildcard $(REPO_DIR)/.venv/bin/python),$(REPO_DIR)/.venv/bin/python,python3)

PDFLATEX ?= pdflatex
BIBTEX   ?= bibtex

# The three manuscript variants. paper = WSAJ submission (double-spaced,
# line-numbered); paper-nolineno = clean single-spaced preprint (no line
# numbers); paper-arxiv = elegant arXiv-style preprint.
PAPER_TEX := main main-nolineno main-arxiv
PAPER_PDF := $(addsuffix .pdf,$(PAPER_TEX))

.PHONY: experiment experiment-synthetic paper paper-nolineno paper-arxiv papers all clean test figures

all: experiment papers

experiment:
	cd $(REPO_DIR) && $(PYTHON) pipeline.py --output-dir outputs

experiment-synthetic:
	cd $(REPO_DIR) && $(PYTHON) pipeline.py --output-dir outputs --force-synthetic

figures:
	cd $(REPO_DIR) && $(PYTHON) figures.py --output-dir outputs

test:
	cd $(REPO_DIR) && $(PYTHON) -m pytest tests/ -q

# Named targets that each build a single manuscript PDF.
paper: main.pdf
paper-nolineno: main-nolineno.pdf
paper-arxiv: main-arxiv.pdf

# All manuscript variants (WSAJ submission, clean preprint, arXiv preprint).
papers: $(PAPER_PDF)

# Build a manuscript PDF from its .tex source: pdflatex -> bibtex -> pdflatex
# twice, so cross-references and citations settle.
$(PAPER_PDF): %.pdf: %.tex references.bib body.tex abstract.tex backmatter.tex preamble-shared.tex | figures
	@if command -v $(PDFLATEX) >/dev/null 2>&1; then \
		cd $(PAPER_DIR) && \
		$(PDFLATEX) -interaction=nonstopmode $* && \
		$(BIBTEX) $* && \
		$(PDFLATEX) -interaction=nonstopmode $* && \
		$(PDFLATEX) -interaction=nonstopmode $*; \
	else \
		echo "$(PDFLATEX) not found; install a TeX distribution to build paper/*.tex"; \
	fi

clean:
	cd $(PAPER_DIR) && rm -f *.aux *.bbl *.blg *.log *.out *.toc *.pdf *.spl
