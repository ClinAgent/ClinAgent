"""Audit Cleveland data and select a CPU model using development folds only."""

import argparse
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter

# Bound native pools before importing numerical libraries.
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, precision_score
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits
from xgboost import XGBClassifier

from aegishealth.data import CATEGORIES, FEATURES, NUMERIC, load_dataset, preprocessor

SEED = 42


def candidates():
    return {
        "dummy": DummyClassifier(strategy="prior"),
        "logistic_c0.1": LogisticRegression(C=0.1, max_iter=2000),
        "logistic_c1": LogisticRegression(C=1, max_iter=2000),
        "logistic_c10": LogisticRegression(C=10, max_iter=2000),
        "random_forest": RandomForestClassifier(
            n_estimators=200, min_samples_leaf=3, max_features="sqrt", n_jobs=2, random_state=SEED
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=200, min_samples_leaf=3, n_jobs=2, random_state=SEED
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=100, max_leaf_nodes=7, l2_regularization=2, random_state=SEED
        ),
        "rbf_svm": CalibratedClassifierCV(
            SVC(C=1, kernel="rbf"), cv=3, method="sigmoid", ensemble=False
        ),
        "xgboost": XGBClassifier(
            n_estimators=150,
            max_depth=2,
            learning_rate=0.04,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=3,
            tree_method="hist",
            device="cpu",
            n_jobs=2,
            eval_metric="logloss",
            random_state=SEED,
        ),
    }


def run(data_path, output, reports):
    output, reports = Path(output), Path(reports)
    output.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    df = load_dataset(data_path)
    X, y = df[FEATURES], (df.num > 0).astype(int)
    train_ids, test_ids = train_test_split(
        np.arange(len(df)), test_size=0.2, stratify=y, random_state=SEED
    )
    Xtrain, ytrain = X.iloc[train_ids], y.iloc[train_ids]
    audit = {
        "source": "https://archive.ics.uci.edu/dataset/45/heart+disease",
        "sha256": hashlib.sha256(Path(data_path).read_bytes()).hexdigest(),
        "shape": list(df.shape),
        "duplicates": int(df.duplicated().sum()),
        "missing": df.isna().sum().to_dict(),
        "original_target_counts": df.num.value_counts().sort_index().to_dict(),
        "binary_target_counts": y.value_counts().sort_index().to_dict(),
        "development_rows": len(train_ids),
        "holdout_rows": len(test_ids),
        "development_summary": Xtrain.describe().to_dict(),
        "development_category_counts": {
            f: Xtrain[f].value_counts().sort_index().to_dict() for f in FEATURES
        },
        "development_spearman": Xtrain[NUMERIC].corr(method="spearman").round(4).to_dict(),
        "development_category_target_rates": {
            f: Xtrain.assign(target=ytrain).groupby(f).target.agg(["count", "mean"]).to_dict()
            for f in CATEGORIES
        },
        "development_target_association": Xtrain[NUMERIC]
        .corrwith(ytrain, method="spearman")
        .to_dict(),
    }
    (reports / "data_audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n")
    cv = list(
        RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED).split(Xtrain, ytrain)
    )
    results = []
    for name, estimator in candidates().items():
        pipeline = Pipeline([("preprocess", preprocessor()), ("classifier", estimator)])
        with threadpool_limits(limits=2):
            scores = cross_validate(
                pipeline,
                Xtrain,
                ytrain,
                cv=cv,
                n_jobs=1,
                scoring={
                    "auc": "roc_auc",
                    "brier": "neg_brier_score",
                    "accuracy": "accuracy",
                    "precision": make_scorer(precision_score, zero_division=0),
                    "recall": "recall",
                    "f1": "f1",
                },
                error_score="raise",
            )
        row = {"model": name}
        for metric in ["auc", "brier", "accuracy", "precision", "recall", "f1"]:
            values = scores[f"test_{metric}"] * (-1 if metric == "brier" else 1)
            row[metric] = float(values.mean())
            row[metric + "_std"] = float(values.std())
            row[metric + "_folds"] = values.tolist()
        row["mean_fit_seconds"] = float(scores["fit_time"].mean())
        results.append(row)
        print(f"{name}: AUC={row['auc']:.4f}, Brier={row['brier']:.4f}", flush=True)
    # Fixed rule: highest mean AUC; Brier breaks exact ties. Holdout is not consulted.
    ranked = sorted(results, key=lambda r: (-r["auc"], r["brier"]))
    winner = ranked[0]["model"]
    pipeline = Pipeline([("preprocess", preprocessor()), ("classifier", candidates()[winner])])
    with threadpool_limits(limits=2):
        pipeline.fit(Xtrain, ytrain)
        pipeline.predict_proba(Xtrain.iloc[:1])
        timings = []
        for _ in range(30):
            start = perf_counter()
            pipeline.predict_proba(Xtrain.iloc[:1])
            timings.append(perf_counter() - start)
    joblib.dump(pipeline, output / "model.joblib")
    joblib.dump(pipeline.named_steps["preprocess"], output / "preprocessor.joblib")
    joblib.dump(
        pipeline.named_steps["preprocess"]
        .named_transformers_["numeric"]
        .named_steps["standardscaler"],
        output / "scaler.joblib",
    )
    # Raw background rows allow explanations in original 13-feature space.
    joblib.dump(
        Xtrain.sample(n=min(32, len(Xtrain)), random_state=SEED), output / "background.joblib"
    )
    np.savez(output / "split.npz", train=train_ids, test=test_ids)
    report = {
        "selected_model": winner,
        "selection_rule": "highest mean CV ROC-AUC; Brier tie-break",
        "seed": SEED,
        "folds": 5,
        "repeats": 3,
        "holdout_evaluated": False,
        "model_bytes": (output / "model.joblib").stat().st_size,
        "warm_prediction_median_ms": float(np.median(timings) * 1000),
        "candidates": ranked,
        "data_sha256": audit["sha256"],
        "features": FEATURES,
    }
    (reports / "model_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "metadata.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Selected {winner}; saved artifacts to {output}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/processed.cleveland.data"))
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()
    run(args.data, args.output, args.reports)


if __name__ == "__main__":
    main()
