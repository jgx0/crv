# Zenodo submission guide — the *paper* (preprint)

This mints a DOI for the **paper itself** (distinct from your code deposit,
`10.5281/zenodo.21924168`). Everything below is copy-paste ready. File to
upload: **`paper/main-arxiv.pdf`**.

Go to <https://zenodo.org> → sign in with `27goldsteinj@millburn.org` → **New
upload** → **Publication** (not Software).

---

## 1. Basic information

| Field | Fill in |
|---|---|
| **Resource type** | Publication → **Preprint** |
| **Title** | Challenge Run Value (cRV): quantifying strategic value in MLB's ABS challenge era |
| **Publication date** | 2026-08-13 |
| **License** | **Creative Commons Attribution 4.0 International** (CC BY 4.0) |
| **Access** | Open Access |

## 2. Creators

Add creator:

| Field | Value |
|---|---|
| Name | Goldstein, Jacob |
| Type | Personal |
| Affiliation | Millburn High School, Millburn, NJ, United States |
| ORCID | 0009-0004-2659-1256 |
| Email (optional) | 27goldsteinj@millburn.org |

## 3. Description

**Type:** Abstract. Paste this (plain text, no LaTeX):

```
We introduce Challenge Run Value (cRV), a pitch-level metric for valuing
Automated Ball-Strike (ABS) challenges in Major League Baseball. Unlike
framing metrics, which measure physical receiving skill under human umpiring,
cRV treats the challenge as a scarce strategic resource whose value depends on
when it is spent, whether it succeeds, and which future options it forgoes.
The model combines run-expectancy deltas from count- and plate-appearance-
ending state changes with a time-decaying, scarcity-weighted penalty for
failed challenges, calibrated against an empirically derived RE288
run-expectancy surface built from public Statcast data. A central
methodological contribution is the valuation of terminal outcomes: challenges
that convert a called strike three into ball four (or the reverse) end the
plate appearance and must be priced from the resulting base/out state and runs
scored rather than zeroed. We implement a reproducible five-module pipeline
(ingestion, event isolation, alternate-state generation, RE288 mapping, and
scoring) with game-clustered bootstrap uncertainty, leverage stratification,
and sensitivity analysis. Applying the model to the 1,971 plate-appearance-
ending challenges recoverable from the 2026 regular season through August 12,
we estimate a mean cRV of 0.159 runs per challenge (95% CI [0.147, 0.172]);
catchers generate roughly two-and-a-half times the per-challenge value of
batters (0.231 versus 0.088). Zeroing terminal states would instead drive the
aggregate negative (-0.016), inverting the sign of the result. The metric
gives teams a principled basis for deciding when to spend a scarce challenge
and for separating high-leverage conversion skill from reckless early usage.
```

## 4. Keywords

```
run expectancy
opportunity cost
catcher framing
sabermetrics
decision quality
resource allocation
```

(One per line — Zenodo auto-turns them into tags.)

## 5. Related identifiers (optional but recommended)

Link the code deposit so paper and code point at each other:

| Field | Value |
|---|---|
| Relation | **Is supplemented by** |
| Identifier | 10.5281/zenodo.21924168 |
| Scheme | DOI |
| Resource type | Software |

## 6. Funding

Leave blank (or "No external funding supported this work." in the Notes).

## 7. Files

1. Click **Upload files** → select `paper/main-arxiv.pdf`.
2. (Optional) also upload `README.md` so the record page previews the
   reproduction instructions.

## 8. Publish

1. **Save draft** → preview the landing page.
2. Click **Publish**. This is permanent and mints
   `10.5281/zenodo.XXXXXXX`.
3. Turn **Versioning ON** so later revisions (e.g., an accepted camera-ready)
   become v2, v3, … under the same DOI.

---

## After publishing

- **ORCID:** because your Zenodo account is linked to ORCID
  (`0009-0004-2659-1256`), the work auto-appears under **Works** with type
  **Preprint**. If it doesn't, add manually: ORCID → Works → **+ Add** →
  **Add DOI** → paste the new DOI → work type **Preprint**.
- **Paste the new DOI back to me** and I'll add a `@misc` entry to
  `references.bib` (for citing the preprint externally / on your CV) and update
  the data-availability text if you want.
- **Share:** use `https://doi.org/10.5281/zenodo.XXXXXXX` everywhere — CV,
  college applications, and the SSAC/CMSAC/NESSIS submissions (see
  `paper/CONFERENCE_PREP.md`).

> Note: keep the paper DOI for external citation only — the manuscript does not
> self-cite its own preprint DOI.
