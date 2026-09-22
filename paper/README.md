# AegisHealth research manuscript

- `main.tex`: IEEEtran conference manuscript with the requested section structure.
- `references.bib`: published references only; no arXiv entries. The UCI entry is
  a primary dataset citation, not a research paper.
- `main.pdf`: compiled, visually checked two-column manuscript.
- `figures/orchestration.mmd`: editable Mermaid description of actual runtime flow.
- `figures/architecture.tex`: vector TikZ figure embedded in the manuscript.
- `generate_results.py`: regenerates numerical tables from committed project reports.
- `generated/derived_metrics.json`: labeled-set Recall@2 and partial-response
  latency derived from saved results; not new experiments.
- `sources.md`: verification links and the scope of each citation.

## Build

Run from the repository root with Python 3 and Tectonic installed:

```sh
python3 paper/generate_results.py
tectonic paper/main.tex
python3 paper/check_manuscript.py
```

Alternatively use a TeX Live installation with IEEEtran, TikZ, and BibTeX:

```sh
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Tectonic downloads required TeX packages on its first run. Python generation uses
only the standard library and does not run models, access patient data, or call a
cloud provider. Regenerating tables does not automatically rewrite narrative
numbers: the check script verifies the current abstract, bibliography keys, and
selected numerical claims, and reviewers must review any changed reports.

## Editorial decisions and submission requirements

The implementation and saved experiments at commit `5b3eec3` are the technical
source of truth. The reference prompt was adapted to avoid claiming a deployed
XGBoost model, five autonomous LLMs, concurrent prediction/SHAP, local generative
inference, demonstrated hallucination reduction, or measured successful cloud
latency. XGBoost remains a measured comparator with its objective documented.

`Template- paper-ieee.docx` was not supplied or found in the project, Codex
attachments, or Downloads. The manuscript therefore uses unmodified IEEEtran
conference geometry rather than claiming an exact match to an unseen template.
Author names and affiliations are deliberately omitted because none were
provided. Add the real author block and check the chosen venue's page limit,
author guidelines, disclosure requirements, and template before submission.

The user's final request for citations overrides the reference prompt's empty
References instruction. Sources are paraphrased with numbered IEEE citations;
there are no invented direct quotations. All cited research is published in
IEEE, Elsevier, Nature, ACM, NeurIPS, or ACL venues. No preprints are cited.

The 200-word abstract and measured results are ready for author review. This is a
research prototype paper, not a claim of clinical deployment or prospective
validation. Further experiments are explicitly labeled future work. Formatting
alone does not establish acceptance or scientific validation.
