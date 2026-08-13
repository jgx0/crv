# Zenodo deposit — step-by-step

The upload package is ready at `deposit/crv-code-and-validation-corpus.zip`
(15 files: pipeline source, tests, README, requirements, the synthetic
validation corpus, and the MIT license). Follow these steps to publish it and
mint a DOI.

## 1. Create / link your account

1. Go to <https://zenodo.org> and sign in (use `27goldsteinj@millburn.org`).
2. Link your ORCID (`0009-0004-2659-1256`) under **Account → Linked accounts**.
3. Verify your e-mail.

## 2. Start a new upload

1. Click **New upload** (green button).
2. Choose **Software** as the upload type (it is code + a small validation corpus).

## 3. Fill in the metadata

Copy-paste these fields exactly:

| Field | Value |
|---|---|
| **Title** | `Challenge Run Value (cRV): analysis code and synthetic validation corpus` |
| **Creators → Name** | `Goldstein, Jacob` |
| **Creators → Affiliation** | `Millburn High School` |
| **Creators → ORCID** | `0009-0004-2659-1256` |
| **License** | `MIT License` |
| **Access right / Visibility** | `Open Access` |
| **Publication type** | `Software` |

**Description** (paste as-is):

> Analysis code and synthetic validation corpus for the manuscript "Challenge
> Run Value (cRV): quantifying strategic value in MLB's ABS challenge era"
> (Journal of Quantitative Analysis in Sports). cRV is a run-denominated
> metric for valuing Automated Ball-Strike (ABS) challenges in Major League
> Baseball, combining RE288 run-expectancy deltas with a time-decaying,
> scarcity-weighted opportunity-cost penalty for failed challenges.
>
> The deposit contains the five-module Python pipeline (ingestion, event
> isolation, alternate-state generation, RE288 mapping, scoring) plus
> validation/analysis, and the deterministic synthetic validation corpus that
> unit-tests every state-transition path. Live Statcast inputs are fetched at
> runtime through `pybaseball`; no MLB data is redistributed.
>
> Reproduction: `pip install -r requirements.txt`, then
> `python pipeline.py --output-dir outputs` (live) or
> `python pipeline.py --output-dir outputs --force-synthetic` (offline corpus),
> and `python -m pytest tests/ -q`.

**Keywords** (one per line): `sabermetrics`, `baseball`, `run expectancy`,
`ABS challenge`, `Statcast`, `reproducibility`.

**Related / alternate identifiers** (optional but recommended):
- Relation: `is supplemented by this upload` → Identifier: `https://github.com/jgx0/crv`

## 4. Upload the files

- Upload **`deposit/crv-code-and-validation-corpus.zip`** (the single archive).
- *Optional:* also upload the repo's top-level `README.md` and
  `synthetic_validation_corpus.csv` separately so the record page renders the
  README and shows the corpus inline. (The corpus is also inside the zip.)

## 5. Publish

1. Click **Save draft** and review.
2. Click **Publish**. This is permanent and mints the DOI
   (`10.5281/zenodo.XXXXXXX`). You can add a version later but cannot retract it.

## 6. After publishing — wire the DOI into the paper

**DONE.** The record is published and mints the DOI
**`10.5281/zenodo.21924168`** (resolves to
<https://zenodo.org/records/21924168>). The `@misc{goldstein2026crv}` entry is
in `paper/references.bib` and the `paper/declarations.md` data-availability
statement carries the DOI.

> **Blind-review note:** keep the manuscript's Data availability wording as
> "released on acceptance" *until* the manuscript is accepted; only the
> camera-ready / declarations template carries the real DOI. When the
> manuscript is accepted, cite `\citep{goldstein2026crv}` in the
> "Reproducing the results" section of `paper/body.tex` and rebuild.
