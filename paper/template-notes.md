# Supplied IEEE Access reference

Reference: repository-root `Template- paper-ieee.docx`.
SHA-256: `fe004c3f782287c7bcf25367726c82bc86b5485d475b1b33d59494fdcc701062`.
The original file is unchanged and is not redistributed with the manuscript.

The reference is a populated published article, not a blank author template.
Its Word conversion contains 64 continuous layout sections, 39 inline images,
and 23 rendered pages, including conversion-induced blank areas and displaced
content. It supplies visual direction, not scientific evidence for AegisHealth.
Its plant-disease results, authors, DOI, acceptance dates, references, and volume
identifiers have not been imported into this paper.

## Observed design and LaTeX mapping

| Reference feature | Adaptation in `access-layout.sty` |
|---|---|
| 8 × 10.875 inch portrait page | Same physical page size |
| Effective text left edge approximately 0.5 inch | 0.5 inch left/right margins |
| Large left-aligned blue Tahoma title, 22 pt | 22 pt sans-serif title, blue `0073AE` |
| Full-width abstract and index terms before columns | Full-width title/abstract/terms block |
| Times New Roman body, 10 pt | IEEEtran Times-compatible 10 pt body |
| Blue uppercase numbered main headings | Blue uppercase Roman-numbered headings |
| Compact uppercase subsection headings | Lettered sans-serif subsection headings |
| Two-column prose; figures can span both columns | Two columns with a 0.24 inch gutter; wide architecture and holdout plots |
| Small numbered figure and table captions | Small captions with blue labels |
| Running header rule and page furniture | AegisHealth running header and ordinary page numbers |
| Bracketed numerical citations and compact references | IEEEtran BibTeX bibliography retained |

The conversion's unusual internal margins, manual line fragments, 64 section
breaks, and misplaced final table are not reproduced. LaTeX handles text flow
and floats natively. Journal logos and publication metadata are omitted because
this manuscript has not been accepted or assigned a DOI. Author details remain
absent until real names and affiliations are supplied. This is a visual
adaptation of the provided article, not a claim to use an official IEEE Access
submission class. The deliverables remain LaTeX and PDF, as previously requested.

## Evidence and graph policy

Five graph files are generated directly from the existing JSON reports. They
show the nine-model development comparison, holdout metrics and raw confusion
counts, six-query retrieval diagnostics, all thirteen SHAP contributions for one
synthetic input, and ten partial local HTTP response times. Error bars denote
fold standard deviations, not confidence intervals. Retrieval judgments are
development seed labels. Cloud synthesis never completed in the saved timing
experiment. No ROC coordinates, new experiments, clinician results, or
hallucination measurements are fabricated.

The application now uses OpenRouter at commit `a9b2ac7`. The evaluation remains
the earlier recorded snapshot at `5b3eec3`; provider migration is not evidence
of improved clinical quality or latency.
