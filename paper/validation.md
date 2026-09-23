# Manuscript validation — 23 September 2026

- Supplied `Template- paper-ieee.docx` rendered and inspected for visual direction.
  The original file's SHA-256 is recorded in `template-notes.md` and unchanged.
- Tectonic 0.15.0 compiled IEEEtran with the local Access-style layout adaptation.
- Output: seven pages, 576 × 783 points (8 × 10.875 inches), two-column body,
  full-width title/abstract/terms, blue headings, and template-derived captions.
- All seven final pages rendered with Poppler and visually inspected after the
  final overflow and page-size corrections. Figures, equations, tables, headers,
  footers, and references are readable; no clipping or overlap was observed.
- No overfull/underfull boxes, missing characters, unresolved citations, or
  unresolved cross-references in the final TeX log. Fonts are embedded, including
  Times-compatible Nimbus Roman, Nimbus Sans, and chart fonts.
- Nonfatal Tectonic notices: initial TU font substitutions before T1 setup, and
  a repeated BibTeX change-detection warning. All ten bibliography keys resolve,
  and final cross-references and visible bibliography were verified separately.
- The abstract contains exactly 200 whitespace-delimited words, with five Index
  Terms and all requested main sections present.
- Ten references remain cited, using published papers and the primary UCI dataset
  record. No arXiv/preprint entries or template-paper citations were added.
- Five graphs regenerated from committed JSON reports, plus the existing vector
  architecture diagram. Holdout counts reproduce Accuracy/Precision/Recall/F1;
  all nine model means reproduce their fifteen saved fold scores. SHAP additivity
  and partial-response status are asserted by the figure generator.
- `python3 paper/check_manuscript.py` passes, including report checksum checks.
- The OpenRouter implementation change is separated from the older measured
  snapshot. No new training, retrieval experiment, or provider call was performed.
- The LaTeX source archive contains all compilation inputs, vector graphs, and
  a short build README. It excludes the user's populated Word reference, private
  data, credentials, and temporary build/QA files.

Author names, affiliations, funding/ethics disclosures, and a venue-specific
submission check remain author-supplied requirements. This visual adaptation is
not a claim that IEEE Access has accepted or published this manuscript.
