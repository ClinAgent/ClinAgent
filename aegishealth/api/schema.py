from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aegishealth.data import CATEGORIES, FEATURES


class PatientInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    age: Annotated[int, Field(ge=1, le=120)]
    sex: Annotated[int, Field(ge=0, le=1)]
    cp: Annotated[int, Field(ge=1, le=4)]
    trestbps: Annotated[float, Field(ge=40, le=300)]
    chol: Annotated[float, Field(ge=50, le=1000)]
    fbs: Annotated[int, Field(ge=0, le=1)]
    restecg: Annotated[int, Field(ge=0, le=2)]
    thalach: Annotated[float, Field(ge=30, le=250)]
    exang: Annotated[int, Field(ge=0, le=1)]
    oldpeak: Annotated[float, Field(ge=0, le=10)]
    slope: Annotated[int, Field(ge=1, le=3)]
    ca: Annotated[int, Field(ge=0, le=3)] | None
    thal: int | None

    @model_validator(mode="after")
    def original_codes(self):
        for feature, codes in CATEGORIES.items():
            value = getattr(self, feature)
            if value is not None and value not in codes:
                raise ValueError(f"{feature}: use original UCI codes {codes}")
        return self

    def feature_array(self):
        return [getattr(self, name) for name in FEATURES]
