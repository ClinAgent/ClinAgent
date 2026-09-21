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


def test_loads_original_labels_and_missing_markers(tmp_path):
    from aegishealth.data import load_dataset

    rows = [PATIENT + [i % 5] for i in range(303)]
    frame = pd.DataFrame(rows, columns=FEATURES + ["num"])
    frame["chol"] = np.arange(150, 453)
    frame["ca"] = frame.ca.astype(object)
    frame.loc[0, "ca"] = "?"
    path = tmp_path / "cleveland.data"
    frame.to_csv(path, header=False, index=False)
    loaded = load_dataset(path)
    assert loaded.shape == (303, 14)
    assert pd.isna(loaded.loc[0, "ca"])
    assert set(loaded.num) == {0, 1, 2, 3, 4}
    frame.loc[0, "num"] = 5
    frame.to_csv(path, header=False, index=False)
    with pytest.raises(ValueError, match="target"):
        load_dataset(path)


def test_rejects_wrong_dataset_shape(tmp_path):
    from aegishealth.data import load_dataset

    path = tmp_path / "wrong.data"
    pd.DataFrame([PATIENT + [0]]).to_csv(path, header=False, index=False)
    with pytest.raises(ValueError, match="303 x 14"):
        load_dataset(path)
