# Resolve repo root relative to this Makefile so local and CI both work.
PAPER_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_DIR := $(abspath $(PAPER_DIR)/..)

# Prefer the repo virtualenv, which is where matplotlib/pandas actually live.
# Override with `make PYTHON=... ` if you manage environments differently.
PYTHON ?= $(if $(wildcard $(REPO_DIR)/.venv/bin/python),$(REPO_DIR)/.venv/bin/python,python3)

.PHONY: experiment paper paper-review paper-dgruyter all clean test figures

all: experiment paper

experiment:
	cd $(REPO_DIR) && $(PYTHON) pipeline.py --output-dir outputs

experiment-synthetic:
	cd $(REPO_DIR) && $(PYTHON) pipeline.py --output-dir outputs --force-synthetic

figures:
	cd $(REPO_DIR) && $(PYTHON) figures.py --output-dir outputs

test:
	cd $(REPO_DIR) && $(PYTHON) -m pytest tests/ -q

# $(1) = jobname, $(2) = TeX to prepend before \input (empty for a plain build).
# bibtex runs on the jobname, so review and submission .bbl files never collide.
define latex_build
	@if command -v pdflatex >/dev/null 2>&1; then \
		cd $(PAPER_DIR) && \
		pdflatex -interaction=nonstopmode -jobname=$(1) "$(2)\input{main.tex}" && \
		bibtex $(1); \
		cd $(PAPER_DIR) && \
		pdflatex -interaction=nonstopmode -jobname=$(1) "$(2)\input{main.tex}" && \
		pdflatex -interaction=nonstopmode -jobname=$(1) "$(2)\input{main.tex}"; \
	else \
		echo "pdflatex not found; install a TeX distribution to build paper/main.tex"; \
	fi
endef

# Submission copy: figures external, per the JQAS "do not embed" rule.
paper: figures
	$(call latex_build,main,)

# Reading copy: same text, figures inlined. Not for submission.
paper-review: figures
	$(call latex_build,main-review,\def\REVIEW{1})

# Post-acceptance De Gruyter typeset version. dgruyter.sty ships in the
# template directory rather than paper/, so TEXINPUTS has to reach it.
DGRUYTER_DIR := $(REPO_DIR)/JQAS_JQAS_LaTeX-Template-for-Authors

paper-dgruyter: figures
	@if command -v pdflatex >/dev/null 2>&1; then \
		cd $(PAPER_DIR) && export TEXINPUTS="$(DGRUYTER_DIR):$$TEXINPUTS" && \
		pdflatex -interaction=nonstopmode main-dgruyter.tex && bibtex main-dgruyter && pdflatex -interaction=nonstopmode main-dgruyter.tex && pdflatex -interaction=nonstopmode main-dgruyter.tex; \
	else \
		echo "pdflatex not found; install a TeX distribution to build paper/main-dgruyter.tex"; \
	fi

clean:
	cd $(PAPER_DIR) && rm -f *.aux *.bbl *.blg *.log *.out *.toc *.pdf *.spl
