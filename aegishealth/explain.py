"""Explain one patient in original feature space, independent of selected model family."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from threadpoolctl import threadpool_limits

from aegishealth.data import FEATURES, validate


class PatientExplainer:
    """Load trusted local artifacts once; reuse for subsequent patients.

    Permutation SHAP explains positive-class probability through the complete pipeline.
    Mask whole raw features so one-hot columns cannot form invalid category combinations.
    Values are probability contributions, not causal or epidemiological risk factors.
    """

    def __init__(self, artifact_dir="artifacts"):
        folder = Path(artifact_dir)
        required = ["model.joblib", "background.joblib", "metadata.json"]
        if any(not (folder / name).is_file() for name in required):
            raise FileNotFoundError(
                "Missing model artifacts. Run: uv run python -m aegishealth.train"
            )
        self.pipeline = joblib.load(folder / "model.joblib")
        self.background = joblib.load(folder / "background.joblib")
        self.metadata = json.loads((folder / "metadata.json").read_text())
        if self.metadata["features"] != FEATURES:
            raise ValueError("Artifact feature schema does not match application schema")
        self.explainer = shap.Explainer(
            self._predict,
            shap.maskers.Independent(self.background, max_samples=32),
            algorithm="permutation",
            feature_names=FEATURES,
            seed=42,
        )

    def _predict(self, values):
        return self.pipeline.predict_proba(pd.DataFrame(values, columns=FEATURES))[:, 1]

    def explain(self, patient):
        if not isinstance(patient, (list, tuple, np.ndarray)) or len(patient) != len(FEATURES):
            raise ValueError(
                f"Patient must be an array of {len(FEATURES)} values in order: {FEATURES}"
            )
        # bool and numeric-looking strings are rejected, null is an explicit missing value.
        if any(
            v is not None and (isinstance(v, (bool, str)) or not np.isscalar(v)) for v in patient
        ):
            raise ValueError("Patient values must be numeric or null")
        frame = pd.DataFrame([patient], columns=FEATURES, dtype=float)
        validate(frame)
        with threadpool_limits(limits=2):
            explanation = self.explainer(frame, max_evals=10 * (2 * len(FEATURES) + 1), silent=True)
            probability = float(self._predict(frame)[0])
        values = explanation.values[0]
        baseline = float(explanation.base_values[0])
        if not np.isclose(baseline + values.sum(), probability, atol=1e-6):
            raise RuntimeError("SHAP explanation failed probability additivity check")
        contributions = []
        for index, name in enumerate(FEATURES):
            value = frame.iloc[0, index]
            contribution = float(values[index])
            contributions.append(
                {
                    "feature": name,
                    "value": None if pd.isna(value) else float(value),
                    "imputed": bool(pd.isna(value)),
                    "shap_value": contribution,
                    "direction": "increases"
                    if contribution > 0
                    else "decreases"
                    if contribution < 0
                    else "neutral",
                }
            )
        ranked = sorted(contributions, key=lambda item: abs(item["shap_value"]), reverse=True)
        return {
            "model": self.metadata["selected_model"],
            "target": "Cleveland disease presence (num > 0)",
            "disease_probability": probability,
            "predicted_class": int(probability >= 0.5),
            "classification_threshold": 0.5,
            "base_probability": baseline,
            "shap_units": "probability",
            "explanation_method": "permutation SHAP (10 permutations)",
            "top_3_contributors": ranked[:3],
            "top_risk_factors": sorted(
                [c for c in contributions if c["shap_value"] > 0], key=lambda c: -c["shap_value"]
            )[:3],
            "contributions": contributions,
            "limitations": "Research model; not a calibrated future-risk score or diagnosis. "
            "SHAP describes model behavior, not causation. Missing inputs are imputed.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--patient", type=Path, required=True, help="JSON array in original UCI order"
    )
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    try:
        result = PatientExplainer(args.artifacts).explain(json.loads(args.patient.read_text()))
    except (ValueError, FileNotFoundError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
