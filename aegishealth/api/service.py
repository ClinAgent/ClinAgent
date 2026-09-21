"""Typed, deterministic agents orchestrate local analysis and cloud synthesis."""

from time import perf_counter

from aegishealth.explain import PatientExplainer
from aegishealth.rag.store import GuidelineRetriever

LABELS = {
    "age": "age in years",
    "sex": "sex",
    "cp": "chest pain type",
    "trestbps": "resting systolic blood pressure mm Hg",
    "chol": "total cholesterol mg/dL",
    "fbs": "fasting glucose above 120 mg/dL",
    "restecg": "resting ECG category",
    "thalach": "maximum exercise heart rate",
    "exang": "exercise induced angina",
    "oldpeak": "exercise ST depression",
    "slope": "exercise ST segment slope",
    "ca": "fluoroscopy vessel count",
    "thal": "thallium test category",
}
CODES = {
    "sex": {0: "female", 1: "male"},
    "cp": {1: "typical angina", 2: "atypical angina", 3: "non-anginal pain", 4: "asymptomatic"},
    "fbs": {0: "no", 1: "yes"},
    "exang": {0: "no", 1: "yes"},
    "restecg": {0: "normal", 1: "ST-T abnormality", 2: "left ventricular hypertrophy"},
    "slope": {1: "upsloping", 2: "flat", 3: "downsloping"},
    "thal": {3: "normal", 6: "fixed defect", 7: "reversible defect"},
}


def clinical_query(patient, prediction):
    terms = []
    for contributor in prediction["top_3_contributors"]:
        feature = contributor["feature"]
        value = patient[feature]
        if value is None:
            continue  # never describe an imputed value as observed
        display = CODES.get(feature, {}).get(value, value)
        terms.append(f"{LABELS[feature]}: {display}")
    return "ASCVD risk assessment and prevention; " + "; ".join(terms)


class LocalAgents:
    def __init__(self, offline=True):
        self.explainability = PatientExplainer()
        self.rag = GuidelineRetriever(offline=offline)
        # Warm SHAP JIT and model/encoder before the server accepts analysis requests.
        self.explainability.explain([63, 1, 4, 145, 233, 1, 2, 150, 1, 2.3, 2, 0, 7])
        self.rag.retrieve("cardiovascular prevention")

    def analyze(self, patient):
        start = perf_counter()
        prediction = self.explainability.explain(patient.feature_array())
        after_prediction = perf_counter()
        query = clinical_query(patient.model_dump(), prediction)
        evidence = [
            {**item, "evidence_id": f"E{i}"}
            for i, item in enumerate(self.rag.retrieve(query), start=1)
        ]
        return {
            "prediction": prediction,
            "retrieval_query": query,
            "evidence": evidence,
            "timings_ms": {
                "prediction_and_shap": (after_prediction - start) * 1000,
                "retrieval": (perf_counter() - after_prediction) * 1000,
            },
        }
