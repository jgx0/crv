# Getting a DOI for the paper (preprint) and adding it to ORCID

You already have a DOI for the **code + validation corpus**
(`10.5281/zenodo.21924168`). This guide is for the **paper itself** — a
separate record, with its own DOI, so you can cite and share the manuscript
as a preprint before (and after) it is accepted anywhere.

> **Which PDF to deposit:** use `paper/main-arxiv.pdf` (the elegant preprint
> layout). It is self-contained, has no line numbers or journal branding, and
> carries your title block, abstract, and references. `paper/main-nolineno.pdf`
> is the fallback if you want the plainer single-spaced version.

---

## Option A — Zenodo (recommended; you already have the account)

1. Sign in at <https://zenodo.org> with `27goldsteinj@millburn.org`
   (ORCID `0009-0004-2659-1256` should already be linked).

2. **New upload** → choose **Publication** (not Software this time).

3. Fill the metadata:

   | Field | Value |
   |---|---|
   | Resource type | **Preprint** |
   | Title | Challenge Run Value (cRV): quantifying strategic value in MLB's ABS challenge era |
   | Creators | Goldstein, Jacob — Millburn High School — ORCID `0009-0004-2659-1256` |
   | Publication date | 2026-08-13 |
   | Description | Paste the abstract from `paper/abstract.tex` (plain text). |
   | Keywords | run expectancy; opportunity cost; catcher framing; sabermetrics; decision quality; resource allocation |
   | License | **CC BY 4.0** (text; use MIT only for code) |
   | Access | Open Access |

4. **Related identifiers** (optional but good practice): add
   `10.5281/zenodo.21924168` (the code deposit) with relation
   **"Is supplemented by this upload"** — so the paper and the code link to
   each other.

5. **Upload** `paper/main-arxiv.pdf`.

6. **Publish** → you get `10.5281/zenodo.XXXXXXX`.

7. Turn **Versioning ON** on the record so later revisions (e.g., an accepted
   camera-ready version) become `v2`, `v3`, … without a new DOI.

### Alternatives (also mint a preprint DOI)

- **OSF Preprints** (<https://osf.io/preprints>) — free, instant Crossref DOI,
  clean landing page, and auto-syncs to ORCID if you link the account.
- **SSRN** (<https://ssrn.com>) — preprint DOI, but it may ask for an
  institutional affiliation; less common for independent high-school authors.
- **arXiv** (<https://arxiv.org>) — mints `10.48550/arXiv.XXXX.XXXXX`, but a
  first-time submitter needs an **endorsement** from an established arXiv
  author, and the subject area must fit (e.g., `stat.AP` / `econ`). Zenodo is
  faster for you.

---

## Adding the DOI to your ORCID as a preprint

### Automatic (if you used Zenodo or OSF with the account linked)

- Publishing the record auto-pushes the work to ORCID (Zenodo does this when
  your ORCID is linked under **Account → Linked accounts**).
- The work type is mapped automatically: a Zenodo **Preprint** becomes an
  ORCID **Preprint** entry.

### Manual (works for any DOI)

1. Log in at <https://orcid.org>.
2. Scroll to **Works** → **+ Add** → **Add DOI**.
3. Paste `https://doi.org/10.5281/zenodo.XXXXXXX` (your new paper DOI).
4. Confirm the metadata (title, date, and it should auto-resolve the rest).
5. Set **Work type = Preprint**.
6. **Save**.

Check the entry appears under "Works" with a "Preprint" badge and a link back
to the Zenodo/OSF record.

---

## After you have the paper DOI

Paste it back to me and I will, if you want:

- Add a `@misc{goldstein2026crv_preprint}` entry to `paper/references.bib`
  (useful if a *different* paper or your CV needs to cite this one);
- Note it in the WSAJ cover-letter / data-availability text; and
- Rebuild the three PDFs.

> Note: a paper does not usually cite its *own* preprint DOI inside its text,
> so the manuscript itself stays unchanged — the paper DOI is for external
> citation and your ORCID record, not an in-paper self-citation.
