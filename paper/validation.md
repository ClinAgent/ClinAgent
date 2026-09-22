# Manuscript validation — 22 September 2026

- Tectonic 0.17.0 compiled `main.tex` with IEEEtran conference class and BibTeX.
- Output: six US Letter pages in two columns, standard class geometry.
- All six pages rendered with Poppler and visually inspected; changed pages 2
  and 5 were rendered and checked again after final symbol/figure corrections.
- No overfull boxes, missing characters, unresolved citations, or unresolved
  cross-references remain. A long latency equation was split across two lines.
- Fonts are embedded, including Times-compatible Nimbus Roman body fonts.
- Nonfatal logs include underfull spacing notices, preamble TU font fallback
  notices before T1 selection, and an intentionally absent author block. The
  resulting embedded fonts and rendered layout were checked explicitly.
- The abstract contains exactly 200 whitespace-delimited words; five Index Terms
  and all requested section headings are present.
- Ten bibliography entries are cited. Research references use published venue
  records, with no arXiv or preprint entries; UCI is separately a dataset source.
- Numerical tables were regenerated from saved JSON reports. Recorded report
  checksums match. Seed-label Recall@2 is explicitly a derived diagnostic;
  classifier results and cloud-completion counts are not new experiments.
- Source text, BibTeX, Mermaid, TikZ, generated tables, and the PDF are included.

The unavailable Word template cannot be compared. Author identities, affiliations,
venue-specific submission rules, and any required ethical or funding disclosures
must be supplied by the authors. No claim of prospective clinical validation,
measured hallucination reduction, or successful cloud latency is made.
