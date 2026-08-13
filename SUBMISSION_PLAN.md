# JQAS Submission Plan — Challenge Run Value ($cRV$)

**Target:** *Journal of Quantitative Analysis in Sports* (JQAS), an official journal of the
American Statistical Association, published by De Gruyter Brill.
**Portal:** ScholarOne Manuscripts — <https://mc.manuscriptcentral.com/dgjqas>
**Review model:** Double-anonymized (blind both ways).
**Manuscript category:** Research Article.
**Source of truth:** JQAS *Instructions for Authors*, last updated 2025-03-03 (pulled and read
in full; a copy of the extracted text is in the job tmp dir). Everything below is checked
against that document. Where this manuscript currently deviates, it is flagged **[FIX]**.

---

## 0. TL;DR — what "submitting correctly" requires

ScholarOne wants a **package of separate files**, not one PDF:

1. Anonymized manuscript (PDF for review + LaTeX source for production)
2. A **separate, non-anonymized title page** file
3. Each **figure as its own file** (`.eps`/`.tiff`, ≥300 dpi)
4. A **cover letter** to the Editor-in-Chief stating the novelty
5. The **Template for Ethical and Legal Declarations** (COI, funding, data availability,
   author contributions, and — see §6 — any AI/LLM-use disclosure)
6. Metadata entered in the portal: keywords, **JEL codes**, **MSC codes**, up to **4
   suggested reviewers**, word count, table/figure counts, ORCID.

The current repo builds an anonymized manuscript and JQAS-format figures already. The work
left is (a) a short list of formatting fixes, and (b) assembling the non-manuscript pieces
(title page, cover letter, declarations, classification codes, reviewers).

---

## 1. Pre-submission manuscript fixes  *(do these first — all in `paper/`)*

These are real deviations from the IFA found by auditing `body.tex` / `main.tex`:

- [ ] **[FIX] Abstract must be a single paragraph.** IFA: *"an abstract of max. 250 words in
  a single paragraph."* The current abstract in `main.tex` (and the `\abstract{}` in
  `main-dgruyter.tex`) is **three** paragraphs. Merge into one. Word count (~200) is fine
  (limit is 250). While merging, keep abbreviations spelled at first use (ABS ✓, cRV ✓) and
  avoid displayed equations/references (inline symbols like $cRV$ are acceptable, but read it
  once as plain prose).
- [ ] **[FIX] Title — lowercase after the colon (sentence case).** IFA: *"The article title
  and subtitle should be in sentence case. Use lowercase letters after colon."* Current:
  *"Challenge Run Value ($cRV$): Quantifying Strategic Value in MLB's ABS Challenge Era."*
  → *"Challenge Run Value ($cRV$): quantifying strategic value in MLB's ABS challenge era."*
  ("Challenge Run Value" may stay capitalized as the proper name of the metric; everything
  after the colon should be lowercased.)
- [ ] **[FIX] Section headings in sentence case.** IFA: *"Headings should be numbered and in
  sentence case."* `\section` numbering is automatic (✓), but several titles are Title Case.
  Change: `Related Work`→`Related work`, `Data and Pipeline`→`Data and pipeline`,
  `Validation Design`→`Validation design`, `Future Work`→`Future work`. (Subheads like
  "Managerial implications" are already fine.)
- [ ] **Running (short) title, ≤ 75 characters incl. spaces** — needed on the title page
  (§3). Suggested: `Challenge Run Value in MLB's ABS challenge era` (46 chars).
- [ ] **Confirm figures have no frames** and all embedded text is ≥ 6 pt in Arial/Helvetica
  (IFA figure rules). The matplotlib figures use color **and** bar direction to
  encode sign, which satisfies *"use patterning/color instead of grey scales."* Spot-check
  the four `outputs/figures/submission/Figure{1..4}` files.
- [ ] **Tables stay as editable LaTeX** (they are `\input{...tex}` — ✓; IFA forbids tables as
  images/Excel). Remove any vertical rules / shading if present (IFA: *"Avoid color, shading,
  vertical lines"*; booktabs is already rule-light).
- [ ] **Rebuild & re-verify** after edits: `cd paper && make paper && make paper-review &&
  make paper-dgruyter`, then re-run the compliance check (page count 20–30, abstract ≤ 250,
  no undefined refs/citations).

> None of these change the science — they are format-compliance edits. I can apply all of the
> **[FIX]** items in one pass on request.

---

## 2. Anonymization (double-anonymized review)

The manuscript file must contain **no author-identifying information**. Current state is
already blind (`\author{}` empty, acknowledgments "Omitted for blind review", no repo URL).
Before upload, also confirm:

- [ ] No author names/affiliations/emails/ORCID anywhere in the manuscript body or PDF
  **document metadata** (check `Title`/`Author` fields of the compiled PDF).
- [ ] Self-citations are phrased in the third person (no *"in our prior work [X]"* that
  unblinds).
- [ ] The GitHub/repository URL stays out of the manuscript (the only `github.com` string is
  inside the **pybaseball citation** in `references.bib`, which is a third-party tool
  reference — that is fine and does not unblind you).
- [ ] Data Availability in the manuscript says code will be released on acceptance (✓ blind).
  The real deposit/DOI goes in the declarations template and the camera-ready (§6, §8).

---

## 3. Title page  *(separate file, NON-anonymized, upload as "not for review")*

IFA requires a separate title-page file containing:

- [ ] **Title** and **short title** (≤ 75 chars).
- [ ] **Author name(s)**, at least one full given + family name; corresponding author marked
  with `*`. (No author changes are possible after acceptance — get this right now.)
- [ ] **Affiliations**: corresponding author needs email, department, institution, street,
  city, postal code, country; co-authors need department, institution, city, postal code,
  country.
- [ ] **ORCID** for each author (strongly recommended; listed on first page). Register at
  <https://orcid.org> if needed. *You must supply this — I will not invent it.*
- [ ] **Word count**, **number of tables**, **number of figures**, and **whether
  supplementary material is included**.
- [ ] Use an **institutional email** for the corresponding author (IFA: institutional
  addresses gate open-access discounts and authenticity).

> A ready-to-fill `paper/title_page.md` (or `.tex`) can be generated on request with the
> counts auto-filled from the build.

---

## 4. Figures & tables for production

- [ ] Upload **each figure as a separate file**, named `Figure 1`, `Figure 2`, … matching
  their in-text numbering. Accepted: `.jpg`, `.eps`, `.png`, `.tiff`. We have EPS (vector) +
  TIF (600 dpi) in `outputs/figures/submission/` — **EPS is the preferred submission format**;
  keep TIF as the raster fallback.
- [ ] Resolution floor: **300 dpi** half-tone/color at print size, **600 dpi** mixed
  line+raster, **1200 dpi** pure line art. Our TIFs are 600 dpi (✓).
- [ ] **Figure captions** live in the manuscript (the "Figure Legends" section already
  collects them), not baked into the image.
- [ ] In the manuscript, each figure/table is **referred to in the text** and a placement
  hint is given. IFA phrasing for tables: `[Place Table 1 near here]`. Avoid "in Figure 1
  below/above" and don't end the preceding sentence with a colon.
- [ ] **Decision — embedded vs. marker manuscript for review.** `make paper` emits *"[Figure N
  about here]"* markers (production style); `make paper-review` **inlines** the figures and is
  also anonymized. **Recommendation: submit the figures-inlined PDF (`main-review.pdf`) as the
  review manuscript** so reviewers see the art in context, and upload the separate EPS/TIF
  files for production. Both satisfy the IFA; inlined is friendlier to reviewers.

---

## 5. Cover letter  *(required at first submission)*

- [ ] Address to the **Editor-in-Chief**.
- [ ] State the **element of novelty** justifying publication in JQAS. Draft hook: *the
  terminal-outcome valuation result — that zeroing plate-appearance-ending challenges inverts
  the sign of aggregate value (mean $cRV$ +0.143 → −0.031 on 1,914 real 2026 ABS challenges) —
  is a methodological contribution specific to the new ABS-challenge era and not captured by
  existing framing metrics.*
- [ ] Affirm the **submission declaration**: not published elsewhere, not under simultaneous
  consideration, all co-authors approve, corresponding author acts on their behalf.
- [ ] (Optional) note any reviewers to **exclude**.

---

## 6. Ethics, declarations & the AI-use policy  *(Template for Ethical and Legal Declarations)*

Download the **Template for Ethical and Legal Declarations** from the journal's Submit tab,
fill it, and upload it. Its statements are placed between the main text and references in the
typeset article. Fill:

- [ ] **Conflict of interest** — current manuscript declares none → template: *"The authors
  state no conflict of interest."*
- [ ] **Research funding** — none → template default: *"None declared."*
- [ ] **Author contributions** — per CRediT-style roles (no honorary authorship; AI tools
  cannot be authors).
- [ ] **Data availability statement** — see §8; JQAS *requires* this and it must be GDPR-clean.
  Statcast inputs are public via `pybaseball`; recommend depositing the analysis code + the
  deterministic synthetic validation corpus in a **CoreTrustSeal / DataCite repository (e.g.
  Zenodo)** to mint a citable DOI, and cite that dataset in the reference list.
- [ ] **Human/animal subjects** — not applicable; state *"Not applicable"* in Methods and the
  template.
- [ ] **⚠ AI / LLM disclosure — read this carefully.** IFA is explicit: LLMs/AI *cannot be
  credited authors*, and *"if applicable indicate the use of Large Language Models, AI and
  Machine Learning Tools for manuscript preparation in the Template for Ethical and Legal
  Declarations."* This manuscript and its pipeline were developed with substantial AI
  assistance. To submit **honestly and in policy**, you must (a) ensure no AI tool is listed
  as an author, and (b) disclose the AI assistance used in drafting/coding in the template
  (e.g. *"Large-language-model tools were used to assist with drafting and code generation;
  all methods, results, and claims were verified by the author(s), who take full
  responsibility for the content."*). This is your call to word, but it is not optional under
  JQAS policy. The Editorial Board may request raw data — which the reproducible pipeline can
  produce.

---

## 7. Portal metadata to have ready before you start the ScholarOne wizard

- [ ] **Keywords (3–6, lowercase, `;`-separated).** Current: `run expectancy; opportunity
  cost; catcher framing; sabermetrics; decision quality; resource allocation` (6 — ✓
  compliant; the earlier worry about "run expectancy" overlapping the title is *not* a JQAS
  rule, so it can stay).
- [ ] **JEL classification codes** (queried in the wizard; <https://www.aeaweb.org/econlit/jelCodes.php>).
  Candidates: **Z22** (Sports), **Z20** (Sports Economics: General), and a methods code such
  as **C10** or **C13** (econometric/estimation methods). Confirm 2–3.
- [ ] **MSC codes** (<https://www.ams.org/msc>). Candidates: **62P99** (applications of
  statistics), **62-07** (data analysis), and optionally **91A** (game theory) for the
  strategic-resource framing. Confirm 1–3.
- [ ] **Suggested reviewers (up to 4)** — names, institution, country, email; each must be at
  a **different institution and country** from every author. Prepare this list offline.
- [ ] **ORCID**, **institutional email**, word/table/figure counts (mirror the title page).

---

## 8. Research data availability (JQAS takes this seriously)

- [ ] Deposit the analysis code and the deterministic synthetic validation corpus in a
  persistent repository (**Zenodo** recommended → gives a DOI; it is DataCite-backed).
- [ ] Add a **data citation** to `references.bib` (DataCite minimum: Creator, Title, Publisher
  [repository], Year, Identifier [DOI]) and cite it in the text.
- [ ] Keep the manuscript's Data Availability wording blind for review ("released on
  acceptance"); put the real DOI into the declarations template / camera-ready.
- [ ] Note the honest coverage caveat already in the paper: the corpus is a **census of
  terminal (PA-ending) challenges** recoverable from Statcast free-text, not all challenges.

---

## 9. Step-by-step ScholarOne submission (first submission)

1. Create/log in to an account at <https://mc.manuscriptcentral.com/dgjqas> using your
   **institutional email**; link ORCID.
2. Start a new submission → choose type **Research Article**.
3. Enter **title, running head, abstract** (single paragraph) and **keywords**.
4. Select **JEL** and **MSC** codes when prompted.
5. Enter authors & affiliations; mark the corresponding author.
6. Upload files with the correct **designations**:
   - Main Document → anonymized manuscript **PDF** (recommend the figures-inlined
     `main-review.pdf`).
   - Source files → LaTeX (`main.tex`/`main-review.tex`, `body.tex`, `preamble-shared.tex`,
     `references.bib`, any `.sty`) — IFA accepts LaTeX; the PDF is the reference render.
   - Title Page → the non-anonymized title-page file, designation **"not for review."**
   - Figures → `Figure1…4` as separate EPS (and/or TIF) files.
   - Ethical/Legal Declarations template.
   - Cover letter.
7. Add **suggested/excluded reviewers**.
8. Complete submission declarations (originality, no dual submission, all authors approve).
9. **Review the system-generated proof PDF** end-to-end before final submit.
10. Submit. Expect an editorial screening decision (relevance/originality/formal correctness)
    then, if it passes, ≥ 2 anonymous reviewers.

---

## 10. Timeline & post-submission

- **Turnaround (IFA):** first decision ~**3–4 weeks**; revisions returned within **3–6
  weeks**; accepted articles online within **2–4 weeks** of acceptance.
- **Revisions:** submit a **point-by-point reply**, a **tracked-changes** version, **and** a
  clean version.
- **Post-acceptance:** author list & title are **locked** (typos only). Galley proofs come via
  Proof Central. Decide **open access** then — CC-BY-4.0, APC may be **waived/discounted**
  under De Gruyter institutional agreements (check with your library first).
- **Typeset target:** the repo's `make paper-dgruyter` (post-acceptance De Gruyter layout) is
  for your own reference; the publisher typesets from your accepted source.

---

## 11. Final pre-flight checklist

- [ ] Abstract is one paragraph, ≤ 250 words, abbreviations spelled out.
- [ ] Title + all headings in sentence case; headings numbered.
- [ ] Manuscript fully anonymized (body **and** PDF metadata).
- [ ] Separate non-anonymized title page with ORCID, counts, institutional email.
- [ ] Four figures uploaded separately (EPS/TIF, ≥ 300 dpi, no frames, ≥ 6 pt labels).
- [ ] Tables editable (LaTeX), rule-light, no shading/vertical lines.
- [ ] References Harvard style, **no issue numbers** (✓ verified), initials dotted+unspaced,
  every reference cited and vice versa.
- [ ] Cover letter to Editor-in-Chief with novelty statement.
- [ ] Declarations template complete — incl. **AI/LLM-use disclosure** and data availability.
- [ ] JEL + MSC codes and 4 suggested reviewers ready.
- [ ] Data + code deposited (Zenodo DOI) and cited.
- [ ] All three builds compile clean; page count 20–30.

---

*Sources:* JQAS Instructions for Authors (De Gruyter Brill, updated 2025-03-03);
JQAS journal page and ScholarOne portal. Links:
<https://www.degruyterbrill.com/publication/journal_key/JQAS/downloadAsset/JQAS_Instructions%20for%20Authors.pdf>,
<https://mc.manuscriptcentral.com/dgjqas>,
<https://www.degruyterbrill.com/journal/key/jqas/html>.
