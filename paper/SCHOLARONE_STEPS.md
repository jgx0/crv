# ScholarOne submission: step-by-step (JQAS)

Submit at **<https://mc.manuscriptcentral.com/dgjqas>**.

Every file you need is already generated. This guide tells you *which* file
goes *where* in the wizard, and flags the handful of fields only you can fill
in.

---

## 0. What is ready vs. blocked on you

| Item | State |
|---|---|
| Anonymized manuscript (PDF) | ✅ `paper/main.pdf` (30 pp, de-identified) |
| Review copy with inlined figures | ✅ `paper/main-review.pdf` (32 pp) |
| LaTeX source (main + body + bib) | ✅ `paper/*.tex`, `paper/references.bib` |
| Title page ("not for review") | ✅ `paper/title_page.md` |
| Cover letter | ✅ `paper/cover_letter.md` |
| Ethical/legal declarations | ✅ `paper/declarations.md` |
| Figures (EPS + 600-dpi TIF) | ✅ `outputs/figures/submission/Figure{1..5}.{eps,tif}` |
| Tables (editable LaTeX) | ✅ `outputs/tables/*.tex` (11 tables) |
| Zenodo DOI | ✅ `10.5281/zenodo.21924168` |
| 4 suggested reviewers | ⛔ **you**: see §6 |
| AI/LLM-use disclosure wording | ⛔ **you**: approve the draft in `declarations.md` |
| Cover-letter date | ⛔ **you**: set on the day you submit |

---

## 1. ScholarOne account

1. Go to <https://mc.manuscriptcentral.com/dgjqas> and create/enter your
   author account.
2. Under account settings, link your **ORCID** (`0009-0004-2659-1256`) and
   confirm the institutional e-mail `27goldsteinj@millburn.org`.

---

## 2. Start a new submission

1. **New Submission**.
2. **Manuscript type:** *Research Article*.
3. **Title:** `Challenge Run Value (cRV): quantifying strategic value in MLB's
   ABS challenge era` (sentence case, as in the manuscript).
4. **Running/short title (≤75 chars):** `Challenge Run Value in MLB's ABS
   challenge era`.
5. **Abstract:** paste the single-paragraph abstract from `paper/main.tex`
   (223 words, within the 250 limit).

---

## 3. Classifications & keywords

- **JEL codes:** `Z22`, `Z20`, `C10`
- **MSC codes:** `62-07`, `62P99`, `91A80`
- **Keywords:** `sabermetrics`, `baseball`, `run expectancy`, `ABS challenge`,
  `Statcast`, `decision analysis`

---

## 4. Authors

- **Author 1:** Jacob Goldstein
  - Affiliation: Millburn High School, 462 Millburn Avenue, Millburn, NJ 07041,
    United States
  - E-mail: `27goldsteinj@millburn.org`
  - ORCID: `0009-0004-2659-1256`
  - Mark as **corresponding author**.

No other authors.

---

## 5. File upload (the order matters for blind review)

Upload files with these **designations**:

| Designation | File |
|---|---|
| **Main document** (anonymous) | `paper/main.pdf` |
| **Title page** → *"not for review"* | `paper/title_page.md` → export to PDF, or paste its content |
| **Cover letter** | `paper/cover_letter.md` (set the date first) |
| **Figures**: one upload per figure | `outputs/figures/submission/Figure{1..5}.eps` **and** `...tif` (600-dpi) |
| **Tables** | `outputs/tables/*.tex` (11 editable LaTeX tables) |
| **Ethical/legal declarations** | `paper/declarations.md` (after you finalize the AI wording) |
| **Supplementary material** | none (declared "No") |

**Blind-review hygiene:** `main.pdf` contains no author name, affiliation,
ORCID, e-mail, or repo URL. The title page carries all identity and is marked
"not for review." Do **not** upload `main-dgruyter.pdf` (it contains the
author block) or `paper/main-dgruyter.tex`.

---

## 6. Suggested reviewers (blocked on you)

ScholarOne will ask for **4 reviewers**, each at a **different institution and
country** from you. For each, supply: name, institution, country, and e-mail.
I cannot invent these; pick real, active sabermetrics / sports-analytics
researchers (no co-authors, no conflicts).

---

## 7. Declarations to confirm in the wizard

Confirm/attach these (full text drafted in `paper/declarations.md`):

- **Conflict of interest:** none
- **Funding:** none
- **Data availability:** public Statcast data; code + synthetic corpus
  deposited on Zenodo at `10.5281/zenodo.21924168`
- **Human/animal subjects:** not applicable
- **AI/LLM use:** approve the wording in `declarations.md` before upload
  (required by JQAS; no AI tool listed as author)

---

## 8. Final checks before "Submit"

- [ ] Cover-letter date set.
- [ ] Title page has the 4 suggested reviewers (or "none suggested").
- [ ] AI-disclosure wording approved (your own words).
- [x] Zenodo DOI added to the data-availability statement and
      `paper/references.bib` (`10.5281/zenodo.21924168`).
- [ ] `main.pdf` verified de-identified (no name/affiliation/ORCID/repo).
- [ ] 11 tables and 5 figures (EPS + TIF) all attached.

---

## 9. Post-submission

- ScholarOne sends a confirmation e-mail to `27goldsteinj@millburn.org`.
- Track status under **Author center → Submitted manuscripts**.
- If a revision is requested, regenerate the artifacts with
  `python pipeline.py --output-dir outputs` and rebuild
  (`cd paper && make paper paper-review paper-dgruyter`) before resubmitting.
