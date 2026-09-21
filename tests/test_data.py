import numpy as np
import pandas as pd
import pytest
from aegishealth.data import FEATURES, preprocessor, validate

PATIENT = [63, 1, 4, 145, 233, 1, 2, 150, 1, 2.3, 2, 0, 7]


def test_imputation_is_learned_from_training_only():
    train = pd.DataFrame([PATIENT, PATIENT], columns=FEATURES, dtype=float)
    train.loc[1, "age"] = 43
    prep = preprocessor().fit(train)
    patient = train.iloc[:1].copy()
    patient.loc[0, "age"] = np.nan
    patient.loc[0, "thal"] = np.nan
    transformed = prep.transform(patient)
    assert np.isfinite(transformed).all()
    assert transformed[0, 0] == pytest.approx(0)  # median 53 is training mean
    numeric = prep.named_transformers_["numeric"]
    assert numeric.named_steps["simpleimputer"].statistics_[0] == 53
    assert numeric.named_steps["standardscaler"].mean_[0] == 53


@pytest.mark.parametrize(
    "feature,value", [("thal", 2), ("cp", 0), ("ca", 4), ("age", float("inf")), ("ca", 0.5)]
)
def test_rejects_invalid_original_codes(feature, value):
    frame = pd.DataFrame([PATIENT], columns=FEATURES, dtype=float)
    frame.loc[0, feature] = value
    with pytest.raises(ValueError):
        validate(frame)


def test_rejects_wrong_feature_order():
    with pytest.raises(ValueError):
        validate(pd.DataFrame([PATIENT], columns=FEATURES).iloc[:, ::-1])
