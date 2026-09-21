import json

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from aegishealth.data import CATEGORIES, FEATURES, preprocessor
from aegishealth.explain import PatientExplainer

PATIENT = [63, 1, 4, 145, 233, 1, 2, 150, 1, 2.3, 2, 0, 7]


@pytest.fixture(params=["linear", "forest", "xgboost"])
def explainer(tmp_path, request):
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(np.tile(PATIENT, (60, 1)), columns=FEATURES, dtype=float)
    for name, codes in CATEGORIES.items():
        frame[name] = rng.choice(codes, size=len(frame))
    frame["age"] = rng.integers(30, 80, size=len(frame))
    frame["chol"] = rng.integers(150, 350, size=len(frame))
    target = ((frame.age > 55) | (frame.exang == 1)).astype(int)
    models = {
        "linear": LogisticRegression(),
        "forest": RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42),
        "xgboost": XGBClassifier(n_estimators=10, max_depth=2, n_jobs=1, device="cpu"),
    }
    pipeline = Pipeline([("preprocess", preprocessor()), ("classifier", models[request.param])])
    pipeline.fit(frame, target)
    joblib.dump(pipeline, tmp_path / "model.joblib")
    joblib.dump(frame.iloc[:10], tmp_path / "background.joblib")
    (tmp_path / "metadata.json").write_text(
        json.dumps({"features": FEATURES, "selected_model": request.param})
    )
    return PatientExplainer(tmp_path)


def test_shap_additivity_and_ranking(explainer):
    result = explainer.explain(PATIENT)
    assert result["base_probability"] + sum(
        c["shap_value"] for c in result["contributions"]
    ) == pytest.approx(result["disease_probability"], abs=1e-6)
    expected = explainer.pipeline.predict_proba(pd.DataFrame([PATIENT], columns=FEATURES))[0, 1]
    assert result["disease_probability"] == pytest.approx(expected)
    ranked = result["top_3_contributors"]
    assert len(ranked) == 3
    assert [abs(c["shap_value"]) for c in ranked] == sorted(
        [abs(c["shap_value"]) for c in ranked], reverse=True
    )
    assert all(c["shap_value"] > 0 for c in result["top_risk_factors"])
    json.dumps(result, allow_nan=False)


def test_missing_patient_features(explainer):
    patient = PATIENT.copy()
    patient[11:13] = [None, None]
    result = explainer.explain(patient)
    assert [c["feature"] for c in result["contributions"] if c["imputed"]] == ["ca", "thal"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("patient", [[], [None] * 13, [True] * 13, ["1"] * 13, [float("inf")] * 13])
def test_invalid_input(explainer, patient):
    with pytest.raises(ValueError):
        explainer.explain(patient)


def test_missing_artifacts(tmp_path):
    with pytest.raises(FileNotFoundError, match="aegishealth.train"):
        PatientExplainer(tmp_path)
