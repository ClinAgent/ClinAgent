# AegisHealth research manuscript

- `main.tex`: IEEE Access-style manuscript adapted from the supplied Word reference.
- `references.bib`: published references only; no arXiv entries. The UCI entry is
  a primary dataset citation, not a research paper.
- `main.pdf`: compiled, visually checked seven-page manuscript.
- `aegishealth-latex.zip`: self-contained compilation inputs for sharing or Overleaf.
- `figures/orchestration.mmd`: editable Mermaid description of actual runtime flow.
- `figures/architecture.tex`: vector TikZ figure embedded in the manuscript.
- `generate_results.py`: regenerates numerical tables from committed project reports.
- `generate_figures.py`: regenerates five vector PDF / 300 dpi PNG result graphs.
- `access-layout.sty`: supplied-template visual adaptation.
- `template-notes.md`: template measurements, fidelity choices, and graph provenance.
- `generated/derived_metrics.json`: labeled-set Recall@2 and partial-response
  latency derived from saved results; not new experiments.
- `sources.md`: verification links and the scope of each citation.

## Build

Run from the repository root with Python 3, Matplotlib, NumPy, and Tectonic installed:

```sh
python3 paper/generate_results.py
python3 paper/generate_figures.py
tectonic paper/main.tex
python3 paper/check_manuscript.py
```

Alternatively use a TeX Live installation with IEEEtran, TikZ, geometry,
titlesec, fancyhdr, caption, and BibTeX:

```sh
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Tectonic downloads required TeX packages on its first run. Python generation uses
the standard library for tables and Matplotlib/NumPy for graphs. These scripts
do not run models or call a cloud provider. Install Matplotlib in a separate
Python environment if regenerating figures; existing vector figures are committed. Regenerating tables does not automatically rewrite narrative
numbers: the check script verifies the current abstract, bibliography keys, and
selected numerical claims, and reviewers must review any changed reports.

## Editorial decisions and submission requirements

The implementation and saved experiments at commit `5b3eec3` are the technical
source of truth. The reference prompt was adapted to avoid claiming a deployed
XGBoost model, five autonomous LLMs, concurrent prediction/SHAP, local generative
inference, demonstrated hallucination reduction, or measured successful cloud
latency. XGBoost remains a measured comparator with its objective documented.

`Template- paper-ieee.docx` is now supplied. Its IEEE Access visual language is
adapted in `access-layout.sty`: blue title/section headings, full-width abstract
and keywords, two-column text, and compact captions. See `template-notes.md` for
measurements and deliberate differences. The published article's logos, DOI,
authors, dates, and results are not reused. Real author names/affiliations and the
chosen venue's submission requirements still need to be provided.

Current provider configuration is OpenRouter (`a9b2ac7`). Saved evaluation
results remain from `5b3eec3`; the paper explicitly distinguishes the two.

The user's final request for citations overrides the reference prompt's empty
References instruction. Sources are paraphrased with numbered IEEE citations;
there are no invented direct quotations. All cited research is published in
IEEE, Elsevier, Nature, ACM, NeurIPS, or ACL venues. No preprints are cited.

The 200-word abstract and measured results are ready for author review. This is a
research prototype paper, not a claim of clinical deployment or prospective
validation. Further experiments are explicitly labeled future work. Formatting
alone does not establish acceptance or scientific validation.
