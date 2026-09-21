"""Original Cleveland schema, download, validation, and leakage-safe preprocessing."""

from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SOURCE = "https://archive.ics.uci.edu/static/public/45/heart+disease.zip"
FEATURES = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
]
NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak", "ca"]
CATEGORIES = {
    "sex": [0, 1],
    "cp": [1, 2, 3, 4],
    "fbs": [0, 1],
    "restecg": [0, 1, 2],
    "exang": [0, 1],
    "slope": [1, 2, 3],
    "thal": [3, 6, 7],
}
# Broad input sanity limits, not diagnostic cutoffs.
BOUNDS = {
    "age": (1, 120),
    "trestbps": (40, 300),
    "chol": (50, 1000),
    "thalach": (30, 250),
    "oldpeak": (0, 10),
    "ca": (0, 3),
}


def validate(frame):
    if list(frame.columns) != FEATURES:
        raise ValueError(f"Expected features in order: {FEATURES}")
    for name in FEATURES:
        values = frame[name].dropna()
        if not np.isfinite(values).all():
            raise ValueError(f"{name}: values must be finite or missing")
        if name in CATEGORIES and not values.isin(CATEGORIES[name]).all():
            raise ValueError(f"{name}: expected original UCI codes {CATEGORIES[name]}")
        if name in BOUNDS and not values.between(*BOUNDS[name]).all():
            raise ValueError(f"{name}: expected range {BOUNDS[name]}")
        if name in ["age", "ca"] and not (values == np.floor(values)).all():
            raise ValueError(f"{name}: expected whole numbers")
    if frame.isna().all(axis=1).any():
        raise ValueError("A patient cannot have every feature missing")


def load_dataset(path=Path("data/raw/processed.cleveland.data")):
    path = Path(path)
    if not path.exists():
        import io
        import zipfile

        with urlopen(SOURCE, timeout=60) as response:
            archive_bytes = response.read()
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            content = archive.read("processed.cleveland.data")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    frame = pd.read_csv(path, header=None, na_values="?", names=FEATURES + ["num"])
    frame = frame.apply(pd.to_numeric, errors="raise")
    if frame.shape != (303, 14):
        raise ValueError(f"Expected original Cleveland 303 x 14 dataset, got {frame.shape}")
    if frame.num.isna().any() or not frame.num.isin(range(5)).all():
        raise ValueError("Invalid Cleveland target: expected integers 0 through 4")
    validate(frame[FEATURES])
    if frame.duplicated().any():
        raise ValueError("Duplicate records require review before splitting")
    return frame


def preprocessor():
    return ColumnTransformer(
        [
            ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUMERIC),
            (
                "categorical",
                make_pipeline(
                    SimpleImputer(strategy="most_frequent"),
                    OneHotEncoder(
                        categories=list(CATEGORIES.values()),
                        handle_unknown="error",
                        sparse_output=False,
                    ),
                ),
                list(CATEGORIES),
            ),
        ]
    )
