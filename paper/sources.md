# Source verification and claim ledger

Verified 22 September 2026 using Firecrawl search/scrape on publisher, proceedings,
PubMed, and UCI pages. Raw extraction files remain in ignored `.firecrawl/`;
full copyrighted papers are not redistributed. Earlier discovery hits from
arXiv were superseded by the publication records below. Only published versions
appear in the bibliography. Literature claims are paraphrases, not quotations.

| BibTeX key | Published source / verification | Supported manuscript use |
|---|---|---|
| mohan2019 | [IEEE Access publisher record](https://ieeexplore.ieee.org/document/8740989), DOI 10.1109/ACCESS.2019.2923707 | Prior hybrid heart-disease prediction; not a head-to-head score comparison. |
| chen2016 | [ACM KDD publication](https://dl.acm.org/doi/10.1145/2939672.2939785) | Regularized additive-tree objective and XGBoost as a candidate. |
| lundberg2017 | [NIPS 2017 proceedings paper](https://proceedings.neurips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions.pdf) | Additive feature attribution and Shapley formulation; not causal validity. |
| rudin2019 | [Nature Machine Intelligence](https://www.nature.com/articles/s42256-019-0048-x) | Perspective advocating interpretable models in high-stakes settings. |
| ghassemi2021 | [Elsevier / The Lancet Digital Health](https://doi.org/10.1016/S2589-7500(21)00208-9), [PubMed verification](https://pubmed.ncbi.nlm.nih.gov/34711379/) | Limits of explanation as a substitute for clinical validation. Publisher scrape was mostly site chrome; metadata and abstract were verified through PubMed. |
| lewis2020 | [NeurIPS 2020 publication](https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html) | Parametric/nonparametric retrieval-augmented generation. AegisHealth does not reproduce joint training. |
| xiong2024 | [ACL Findings 2024](https://aclanthology.org/2024.findings-acl.372/) | MIRAGE/MedRAG evaluation and dependence on corpus/retriever choices. |
| tang2024 | [ACL Findings 2024](https://aclanthology.org/2024.findings-acl.33/) | Collaborative multi-round medical reasoning; distinguished from this deterministic pipeline. |
| arnett2019 | [Circulation executive-summary DOI](https://doi.org/10.1161/CIR.0000000000000677), [PubMed metadata](https://pubmed.ncbi.nlm.nih.gov/30879339/) | Identity and primary-prevention scope of the indexed historical source. |
| uci | [UCI dataset](https://archive.ics.uci.edu/dataset/45/heart+disease), DOI 10.24432/C52P4X | Primary dataset attribution and original feature schema. This is a dataset reference, not an unpublished paper. |

## Project evidence

| Claim | Repository evidence |
|---|---|
| 303 records, 164/139 labels, missingness, split | `reports/data_audit.json`, `aegishealth/data.py` |
| Nine prespecified configurations, shared folds, selected C=0.1 | `aegishealth/train.py`, `reports/model_comparison.json` |
| Holdout metrics, bootstrap interval, 0/10 complete requests | `reports/evaluation.json`, `aegishealth/evaluate.py` |
| 32-row independent masker, 270-evaluation budget, additivity tolerance | `aegishealth/explain.py` |
| Sequential SHAP → query → retrieval; semaphore before cloud | `aegishealth/api/service.py`, `aegishealth/api/app.py` |
| Default providers and output/citation shape checks | `aegishealth/api/synthesis.py` |
| 140 final chunks, pinned embedding, cosine store | `reports/final_validation.md`, `aegishealth/rag/embeddings.py`, `aegishealth/rag/store.py` |
| Raw recorded example contribution values | `reports/example_explanation.json` |
| Seed Recall@2 and partial median latency | `paper/generate_results.py`, `paper/generated/derived_metrics.json` |

`reports/phase2.md` describes an earlier 202-chunk index. The manuscript uses the
later 140-chunk integration result, not the obsolete index size. Earlier phase-2
retrieval timing is not combined with final HTTP timing. Current UI supports
sanitized Markdown; older reports describing raw escaped rendering precede that
change.

Unmeasured: clinician benefit, hallucination reduction, citation entailment,
prospective or external validity, successful cloud latency, local LLM expense,
load capacity, and comparative benefit of agent decomposition. These are not
reported as established findings.
