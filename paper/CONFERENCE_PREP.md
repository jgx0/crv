# Preparing the paper for SSAC, CMSAC, and NESSIS

This is the step-by-step plan for submitting *Challenge Run Value (cRV)* to the
three research-oriented sports-analytics venues. All three accept work that is
also posted as a preprint (and WSAJ, your journal target, is a different track),
so you can pursue them in parallel. The dates below are current as of
**2026-08-13**; re-check each portal before you submit.

---

## At a glance

| | **SSAC** (MIT Sloan) | **CMSAC** (Carnegie Mellon) | **NESSIS** (New England) |
|---|---|---|---|
| Venue type | Research-paper competition | Conference + poster competition | Statistics symposium |
| Next round | SSAC27 (submit 2026) | Oct 23–24, 2026 | 2027 (biennial) |
| First deliverable | **Abstract** | **Poster abstract** | **Abstract** |
| Deadline | **Oct 1, 2026** 11:59 p.m. ET | ~mid-August 2026 (confirm portal) | Opens **early 2027** |
| Full paper? | Yes, **Dec 4, 2026** (if invited) | No (poster) | No (talk/poster from abstract) |
| Open-source required? | **Yes** (public repo + data) | No | No |
| Student-friendly? | Yes (blind review) | Yes (cash prizes) | Yes (best student poster) |

**Order of operations:** CMSAC (nearest deadline) → SSAC abstract (Oct 1) →
NESSIS (2027). Nothing blocks anything else.

---

## 1. SSAC — MIT Sloan Research Paper Competition

Portal: <https://www.sloansportsconference.com/research-paper-competition>
Track: **Baseball**.

### What to submit (Abstract Phase)

- **≤ 500 words** *including the title and body* — this is the hard limit.
- **Exactly four sections:** Introduction · Methods · Results · Conclusion.
- **Up to 2 figures/tables combined** (e.g., 1 figure + 1 table, or 2 tables).
- A **link to a public repository** containing the data (code encouraged).

### What to prepare

1. **A fresh SSAC abstract.** Do *not* reuse the 154-word manuscript abstract —
   it is too short and lacks the required four-section structure. It must:
   - **Introduction** — the question (how valuable is an ABS challenge, and
     *when* is it worth spending) and why it matters to teams.
   - **Methods** — five-module pipeline, RE288 surface, scarcity-weighted
     opportunity-cost penalty, game-clustered bootstrap.
   - **Results** — mean cRV **0.159** (CI [0.147, 0.172]); catchers 0.231 vs
     batters 0.088; terminal-zeroing flips the sign to −0.016; cRV↔success-rate
     r = 0.72; cWPA by role.
   - **Conclusion** — a principled spend/don't-spend rule for a scarce resource.
2. **Pick the 2 figures/tables.** Recommended: the **player leaderboard**
   (`outputs/figures/leaderboard_top10.pdf`) + the **cWPA-by-role** figure
   (`outputs/figures/challenge_wpa.pdf`). Both are self-explanatory and land the
   "catchers > batters" story without needing the paper.
3. **Open-source repo.** You already have `github.com/jgx0/crv`. Before Oct 1:
   - make the repo **public**,
   - push `main` up to date,
   - confirm `README.md` documents the reproduction command
     (`python pipeline.py --output-dir outputs`) and points to the data,
   - keep the Zenodo code+corpus DOI (`10.5281/zenodo.21924168`) in the README
     as a second, version-frozen link. Statcast is public data, so no
     anonymization is needed.

### If invited (late October)

- Full manuscript due **Dec 4, 2026**. Submit `paper/main.pdf` (or the
  `main-arxiv.pdf` layout) — but check whether SSAC wants the title page on or
  off; the competition reviews blind, so send a **de-identified** copy
  (strip the author block from `main.tex`'s title page) unless told otherwise.

---

## 2. CMSAC — Carnegie Mellon Sports Analytics Conference

Portal: <https://www.cmsaconference.com/> · Conference **Oct 23–24, 2026**,
Pittsburgh, PA.

### What to submit

- A **poster abstract** (the 2025 cycle closed its abstract call ~**Aug 15**;
  the 2026 call is not yet posted — "Registration Opening Soon" — so confirm
  the exact deadline on the portal *now*; it is the nearest of the three).

### What to prepare

1. **A short poster abstract** (~250–400 words): one paragraph each on the
   question, the method, the headline result (mean 0.159; catchers 2.5×
   batters; terminal-zeroing sign flip), and the team takeaway.
2. **A poster** (if accepted). Reuse the figures directly:
   - pipeline overview (`pipeline_diagram`),
   - leaderboard (`leaderboard_top10`),
   - role comparison (`challenger_totals`),
   - sensitivity (`ev_sensitivity`),
   - cWPA by role (`challenge_wpa`).
   The five figures already tell the whole story; a poster is mostly laying
   them out with the abstract text.
3. **Student angle:** CMSAC gives cash prizes for student research — list your
   school affiliation and note it's independent research.

---

## 3. NESSIS — New England Symposium on Statistics in Sports

Portal: <https://www.nessis.org/call.html>

### Timing

- NESSIS is **biennial**: 2025 happened Sept 27, 2025; the next is **2027**.
- Abstract submission **opens early 2027** (the 2025 deadline was July 15, so
  expect a ~mid-2027 deadline). This is the long-horizon target — set a
  calendar reminder for **January 2027**.

### What to prepare (when the call opens)

1. **A statistics-framed abstract** — NESSIS's audience is statisticians, so
   lead with the methodology rather than the baseball story: RE288 estimation,
   the scarcity-weighted penalty as a first-order approximation to the
   optimal-stopping DP, game-clustered bootstrap CIs, and the split-half
   reliability result (r = 0.34) as the honest uncertainty check.
2. **Oral vs poster:** both are considered from the abstract; there is a
   **best student poster** prize, so a poster is a good first entry point.
3. **Reuse** the `main-arxiv.pdf` preprint as the handout/upload if one is
   requested; it is already self-contained and stats-forward.

---

## Shared assets already in the repo

| Asset | Path | Used by |
|---|---|---|
| Full manuscript (WSAJ) | `paper/main.pdf` | SSAC full paper |
| Clean preprint | `paper/main-nolineno.pdf` | any handout |
| Elegant preprint | `paper/main-arxiv.pdf` | preprint DOI / NESSIS |
| Manuscript abstract (154 w) | `paper/abstract.tex` | reference only — not SSAC |
| Figures (5) | `outputs/figures/*.pdf` | SSAC abstract, CMSAC poster |
| Code + corpus DOI | `10.5281/zenodo.21924168` | SSAC open-source |
| Public repo | `github.com/jgx0/crv` | SSAC open-source |

## Caveats

- **Double submission is fine** across these three (they are conferences /
  competitions, not journals). Do **not** simultaneously submit the manuscript
  to another *journal* while WSAJ is reviewing it.
- **Blind review:** SSAC reviews abstracts without author names. Keep the
  abstract itself author-free; the repo link technically identifies you, which
  SSAC accepts (they require the open-source link).
- **Verify dates** on each portal right before you submit — conference calls
  shift year to year, and the CMSAC 2026 call was not posted at the time of
  writing.

---

*Next actions I can do for you: draft the SSAC ≤500-word four-section abstract,
draft the CMSAC poster abstract, or assemble the poster layout.*
