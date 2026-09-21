# Phase 2: local guideline retrieval

Phase 2 implements CPU MiniLM embeddings, LangChain document splitting and
persistent local Chroma retrieval. It adds no generative LLM or API endpoint.

## Source verification

The user-added UCI folder is unchanged. Its `processed.cleveland.data` checksum
matches the Phase 1 copy. It is tabular training data, not guideline evidence.

The user authorized downloading the Executive Summary. The direct AHA PDF URL
returned HTTP 403. Firecrawl extracted the official PDF successfully; its
unmodified UTF-8 text/Markdown output is saved as
`data/knowledge_base/acc_aha_2019_executive_summary.txt`. The separate provenance
JSON in the same directory records extraction time, method and URL.

Source: [AHA Executive Summary PDF](https://www.ahajournals.org/doi/pdf/10.1161/CIR.0000000000000677).
The earlier HTML extraction omitted recommendation tables because they were
images. It was rejected as the index source. The PDF-derived extraction contains
the cholesterol, activity, tobacco and aspirin recommendation tables. Text
extraction can still distort column order, hyphenation, table cells and equations;
source links remain essential for checking consequential details. The title and
length checks are not a completeness or authenticity certificate.

Source SHA-256: `4e5d13566e0eb2522789819554308f3396edab1be25e2090503542f019c364f5`.
Full guideline text and vectors remain local and git-ignored.

## Index and retrieval

- Encoder: `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, normalized vectors.
- Pinned model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- CPU-only PyTorch on Linux/Windows; two encoder threads, batch size 16, two HNSW threads.
- LangChain recursive splitting: maximum 500 characters, target overlap 50;
  separator and PDF-page boundaries can yield smaller overlaps.
- Search corpus: **202 chunks**. Bibliography and following appendices are
  excluded; standalone headings/table headers are omitted. Complete source text
  remains unchanged on disk. No paraphrasing is performed on indexed passages.
- Persistent Chroma at `artifacts/chroma/`, cosine distance, top two matches.
- Each match includes the exact stored text, source filename/DOI/checksum, stable
  chunk ID and start offset. PDF input additionally includes one-based page and
  page-label metadata. The downloaded TXT has character offsets, not invented pages.
- An unchanged source/configuration is a no-op. Changes build a new collection
  and atomically replace the manifest only after all chunks are stored. Failures
  leave the old active collection intact. Old collections are retained for readers;
  rebuild in a fresh index directory to reclaim old storage when readers stop.

## Verification

The combined suite has **43 passing tests**: Phase 1 tests plus document validation,
exact source slices, bibliography/header exclusion, scanned-PDF rejection,
idempotent insertion, persistent queries, lock handling, and failed-update rollback.
Ruff and whitespace checks pass.

The deterministic test encoder is used only for offline unit/integration checks.
The separate smoke run used the actual pinned MiniLM model and the downloaded
AHA text. A fresh process reopened the index with `--offline`, retrieved two
matches per query, verified all character offsets against the source, and checked
that unchanged ingestion did not create duplicate chunks. See
[recorded measurements](phase2_smoke.json).

Warm query median: **5.53 ms** across ten calls.
Encoder/index initialization after imports: **0.196 s**.
Peak process RSS: **624.6 MiB** on this Linux machine.
These measurements exclude interpreter/module startup, network downloads, SHAP,
cloud inference and HTTP. They do not establish the full three-second target.

## Observed relevance and open limitations

The example query “high cholesterol and age over 50” retrieved conditional
cholesterol/statin passages. Exercise and smoking queries retrieved related
activity and tobacco passages. These are smoke observations, not adjudicated
relevance labels or a Precision@k score.

The aspirin query “aspirin primary prevention adults over 70” **missed the explicit
over-70 warning in its top two results**, returning a younger-age conditional
passage and general prevention guidance instead. This is a known limitation of
the dense top-two baseline, not a passed clinical safety check. Future evaluation
must include age qualifiers, negation, contraindications and missing patient
information; reranking or broader context may be necessary before clinical use.
Formal Precision@k evaluation remains in Phase 5 as requested.

The future synthesis layer must preserve each passage's conditions. The Cleveland
`chol` input is total cholesterol, not LDL cholesterol; neither diabetes status
nor a ten-year ASCVD risk estimate can be assumed from absent fields. Retrieved
text is evidence content, not executable instructions. It cannot establish that
a medication is appropriate for a patient.

## Run and next gate

```bash
uv sync --locked --extra rag
uv run --extra rag python -m aegishealth.rag ingest --source data/knowledge_base/acc_aha_2019_executive_summary.txt --offline
uv run --extra rag python -m aegishealth.rag query "high cholesterol and age over 50" --offline
uv run --extra rag pytest -q
```

Omit `--offline` on a new machine for the first MiniLM download. The guideline TXT
must be supplied separately on another checkout because it is intentionally not
committed. The optional `--index` flag selects a different persistent directory.

Phase 2 is complete as a research retrieval baseline. Per the user's phase gates,
Phase 3 (FastAPI and cloud-LLM orchestration) waits for confirmation.
