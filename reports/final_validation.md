# AegisHealth: integrated validation

## Delivered behavior

Phases 3–5 are implemented: FastAPI orchestration, Groq/OpenAI cloud-only synthesis,
a responsive React/Vite/Tailwind/Recharts dashboard, and a reproducible evaluation
command. No API key was available during this run, so live cloud generation and
full end-to-end latency remain unverified. The application explicitly returns
partial results without substituting a canned clinical summary.

The backend validates all 13 named inputs, warms the saved classifier/SHAP/MiniLM
at startup, serializes local work, retrieves exact passages, and checks provider
JSON for three sentences and valid evidence IDs. Cloud timeout, rejection,
malformed output, truncation and citation errors are covered with an HTTP mock
transport. This is contract testing, not a live cloud experiment or validation of
clinical assertions. The Groq default is cloud-hosted GPT-OSS 20B; an OpenAI
provider option is also implemented. No LLM inference occurs on this device.

The frontend was built using the requested frontend-design skill. It includes a
validated intake form, explicit synthetic-example loading, a probability gauge,
signed SHAP bars with an accessible value list, exact raw guideline excerpts,
and a separate synthesis block. Editing measurements invalidates old results.
Fonts are bundled locally; keys and patient data are not persisted in the browser.
The evidence is escaped text, so document HTML or scripts are not executed.

## Holdout model metrics

The original fixed split and dataset checksum were verified. The 61 holdout rows
were excluded from model selection and preprocessing fit. The selected model
remains logistic regression with C=0.1; it was not retuned after holdout evaluation.

| Metric | Result |
|---|---:|
| Accuracy | 0.8852 |
| Precision | 0.8387 |
| Recall | 0.9286 |
| F1 | 0.8814 |
| ROC-AUC | 0.9610 |
| Brier score | 0.0869 |
| True negatives / false positives | 28 / 5 |
| False negatives / true positives | 2 / 26 |

Threshold: 0.5. A 1,000-resample percentile bootstrap gives a descriptive ROC-AUC
95% interval of approximately 0.902–0.999. This interval concerns this small
holdout only and does not quantify transportability to other populations. The
classifier estimates existing disease presence, not a ten-year ASCVD risk score.

## Retrieval evaluation

The final index has 140 chunks. Integration testing exposed publication and
methodology passages being retrieved; these sections were excluded without
rewriting retained text or losing source offsets. Recommendation-specific source
IDs stayed valid. Filtering and query development occurred during implementation,
so the following diagnostic set is not an unbiased benchmark.

Six source-grounded seed relevance judgments were recorded in
`evaluation/retrieval_labels.json`. They are implementation-time judgments, not
independent clinician annotations. Precision@2 is the number of unique retrieved
IDs judged directly relevant divided by 2; missing and duplicate hits do not
receive credit. A query with only one labeled relevant chunk cannot exceed 0.5.

| Query topic | Precision@2 |
|---|---:|
| Weekly physical activity | 1.0 |
| Aspirin for adults over 70 | 0.0 |
| Aspirin with bleeding risk | 1.0 |
| Dietary pattern | 0.0 |
| Obesity and weight loss | 1.0 |
| LDL-C at least 190 mg/dL | 0.5 |
| **Mean** | **0.5833** |

The age-specific aspirin warning is still missed. Some matches provide indirect
context or captions rather than a direct answer. Neither semantic similarity nor
valid citation IDs guarantee appropriate advice. The corpus is a historical
primary-prevention guideline, while the model uses diagnostic-test features;
that mismatch also limits evidence relevance. Broader independent labels,
qualifier-aware retrieval and clinical review are needed before clinical use.

## HTTP latency

Ten actual HTTP requests with a synthetic example returned real predictions,
SHAP and evidence, but every synthesis result was `provider_not_configured`.
Complete successful requests: **0/10**. Complete-call median and p95: **not
measurable**. The **under-three-second target is not demonstrated**. Fast partial
responses are deliberately excluded from success calculations.

After setting a key and restarting the backend, rerun:

```bash
uv run --extra rag --extra api python -m aegishealth.evaluate --api-url http://127.0.0.1:8000 --requests 10
```

The JSON report contains all individual samples and the precise pass criterion.
Even ten successful fast calls would establish only a small local experiment,
not load-tested clinical-environment performance.

## Verification and local access

- Python suite: 57 passing tests, covering prior phases, API contracts, input
  rejection, source-boundary offsets, and evaluation success accounting.
- TypeScript check and production Vite build pass; Ruff and whitespace checks pass.
- Three Playwright tests pass against the real local API: successful local analysis,
  native field validation, source passages, stale-result invalidation, 390px mobile
  overflow check, and an injected network failure with no fabricated results. A
  complete-summary UI state is verified with an explicit test fixture; that fixture
  is not a real cloud generation.
- Desktop (1440px) and mobile (390px) screenshots were visually reviewed. The
  clipboard-style form, gauge, signed bars and evidence panel render at both sizes.
- The built application is served by the API at `http://127.0.0.1:8000/`.

A dependency emits a Starlette/AnyIO deprecation warning during tests; it did not
fail any checks. The app is a local research prototype without authentication or
production hardening. No deployment or external publication was performed.
