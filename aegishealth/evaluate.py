"""Evaluate the frozen holdout, labeled top-two retrieval, and actual HTTP pipeline."""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from aegishealth.data import FEATURES, load_dataset


def evaluate_model(artifacts=Path("artifacts"), data=Path("data/raw/processed.cleveland.data")):
    frame = load_dataset(data)
    metadata = json.loads((artifacts / "metadata.json").read_text())
    if hashlib.sha256(data.read_bytes()).hexdigest() != metadata["data_sha256"]:
        raise ValueError("Dataset differs from the frozen training data")
    split = np.load(artifacts / "split.npz")
    train, test = split["train"], split["test"]
    if (
        set(train) & set(test)
        or len(set(train)) != len(train)
        or len(set(test)) != len(test)
        or set(train) | set(test) != set(range(len(frame)))
    ):
        raise ValueError("Holdout split is invalid or overlaps training")
    model = joblib.load(artifacts / "model.joblib")
    X, y = frame.iloc[test][FEATURES], (frame.iloc[test].num > 0).astype(int).to_numpy()
    probability = model.predict_proba(X)[:, 1]
    predicted = (probability >= 0.5).astype(int)
    rng = np.random.default_rng(42)
    aucs = []
    for _ in range(1000):
        indices = rng.integers(0, len(y), size=len(y))
        if len(np.unique(y[indices])) == 2:
            aucs.append(roc_auc_score(y[indices], probability[indices]))
    return {
        "model": metadata["selected_model"],
        "holdout_rows": len(test),
        "threshold": 0.5,
        "accuracy": accuracy_score(y, predicted),
        "precision": precision_score(y, predicted, zero_division=0),
        "recall": recall_score(y, predicted, zero_division=0),
        "f1": f1_score(y, predicted, zero_division=0),
        "roc_auc": roc_auc_score(y, probability),
        "roc_auc_bootstrap_95_percent_interval": np.quantile(aucs, [0.025, 0.975]).tolist(),
        "brier": brier_score_loss(y, probability),
        "confusion_matrix_tn_fp_fn_tp": confusion_matrix(y, predicted, labels=[0, 1])
        .ravel()
        .tolist(),
        "dataset_sha256": metadata["data_sha256"],
        "used_for_selection": False,
    }


def precision_at_k(retrieved, relevant, k=2):
    if k < 1:
        raise ValueError("k must be positive")
    return len(set(retrieved[:k]) & set(relevant)) / k


def evaluate_retrieval(labels_path=Path("evaluation/retrieval_labels.json")):
    from aegishealth.rag.store import GuidelineRetriever

    labels = json.loads(labels_path.read_text())
    retriever = GuidelineRetriever(offline=True)
    if labels["source_sha256"] != retriever.manifest["source_sha256"]:
        raise ValueError("Retrieval annotations reference a different guideline export")
    indexed_ids = set(retriever.store.get(include=[])["ids"])
    rows = []
    for item in labels["queries"]:
        if not set(item["relevant_chunk_ids"]) <= indexed_ids:
            raise ValueError(f"Stale relevance labels: {item['id']}")
        retrieved = [s["metadata"]["chunk_id"] for s in retriever.retrieve(item["query"])]
        rows.append(
            {
                **item,
                "retrieved_chunk_ids": retrieved,
                "precision_at_2": precision_at_k(retrieved, item["relevant_chunk_ids"]),
            }
        )
    return {
        "k": 2,
        "mean_precision_at_2": float(np.mean([r["precision_at_2"] for r in rows])),
        "annotation_method": labels["annotation_method"],
        "note": "Singleton relevant sets can attain at most 0.5 Precision@2; this is a small development diagnostic, not clinical validation.",
        "queries": rows,
    }


def evaluate_http(url, requests=10):
    import httpx

    patient = dict(zip(FEATURES, json.loads(Path("examples/patient.json").read_text())))
    rows = []
    with httpx.Client(timeout=35) as client:
        for _ in range(requests):
            start = perf_counter()
            try:
                response = client.post(url.rstrip("/") + "/analyze", json=patient)
                response.raise_for_status()
                body = response.json()
                complete = (
                    body.get("status") == "complete"
                    and body.get("synthesis", {}).get("status") == "complete"
                )
                rows.append(
                    {
                        "seconds": perf_counter() - start,
                        "complete": complete,
                        "synthesis_reason": body.get("synthesis", {}).get("reason"),
                        "http_status": response.status_code,
                    }
                )
            except (httpx.HTTPError, ValueError):
                rows.append(
                    {
                        "seconds": perf_counter() - start,
                        "complete": False,
                        "synthesis_reason": "http_failure",
                    }
                )
    complete_times = [r["seconds"] for r in rows if r["complete"]]
    return {
        "target_seconds": 3,
        "requests": len(rows),
        "complete_requests": len(complete_times),
        "complete_p50_seconds": float(np.median(complete_times)) if complete_times else None,
        "complete_p95_seconds": float(np.percentile(complete_times, 95))
        if complete_times
        else None,
        "target_met": len(complete_times) == requests and all(t < 3 for t in complete_times),
        "criterion": "All requested end-to-end calls must complete with cloud synthesis in under three seconds; no partial response counts as success.",
        "samples": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", help="Running API origin, e.g. http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("reports/evaluation.json"))
    args = parser.parse_args()
    if args.requests < 1:
        parser.error("--requests must be positive")
    result = {
        "ml": evaluate_model(),
        "rag": evaluate_retrieval(),
        "end_to_end": evaluate_http(args.api_url, args.requests)
        if args.api_url
        else {"status": "not_run", "target_met": None},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
