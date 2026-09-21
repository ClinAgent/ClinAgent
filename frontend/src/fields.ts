export type FieldSpec = {
  key: string;
  label: string;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  options?: [number, string][];
  optional?: boolean;
};
export const groups: { title: string; note: string; fields: FieldSpec[] }[] = [
  {
    title: "Patient characteristics",
    note: "Age, sex, and symptoms",
    fields: [
      { key: "age", label: "Age", unit: "years", min: 1, max: 120, step: 1 },
      {
        key: "sex",
        label: "Sex recorded in dataset",
        options: [
          [0, "Female"],
          [1, "Male"],
        ],
      },
      {
        key: "cp",
        label: "Chest pain type",
        options: [
          [1, "Typical angina"],
          [2, "Atypical angina"],
          [3, "Non-anginal pain"],
          [4, "Asymptomatic"],
        ],
      },
    ],
  },
  {
    title: "Resting measurements",
    note: "Use observed values in the units shown",
    fields: [
      {
        key: "trestbps",
        label: "Resting blood pressure",
        unit: "mm Hg",
        min: 40,
        max: 300,
      },
      {
        key: "chol",
        label: "Total cholesterol",
        unit: "mg/dL",
        min: 50,
        max: 1000,
      },
      {
        key: "fbs",
        label: "Fasting glucose above 120 mg/dL",
        options: [
          [0, "No"],
          [1, "Yes"],
        ],
      },
      {
        key: "restecg",
        label: "Resting ECG",
        options: [
          [0, "Normal"],
          [1, "ST–T abnormality"],
          [2, "LV hypertrophy"],
        ],
      },
    ],
  },
  {
    title: "Exercise & diagnostic tests",
    note: "Missing vessel and thallium results use estimated values.",
    fields: [
      {
        key: "thalach",
        label: "Maximum heart rate",
        unit: "bpm",
        min: 30,
        max: 250,
      },
      {
        key: "exang",
        label: "Exercise-induced angina",
        options: [
          [0, "No"],
          [1, "Yes"],
        ],
      },
      {
        key: "oldpeak",
        label: "ST depression",
        unit: "relative to rest",
        min: 0,
        max: 10,
        step: 0.1,
      },
      {
        key: "slope",
        label: "Peak exercise ST slope",
        options: [
          [1, "Upsloping"],
          [2, "Flat"],
          [3, "Downsloping"],
        ],
      },
      {
        key: "ca",
        label: "Major vessels on fluoroscopy",
        optional: true,
        options: [
          [0, "0 vessels"],
          [1, "1 vessel"],
          [2, "2 vessels"],
          [3, "3 vessels"],
        ],
      },
      {
        key: "thal",
        label: "Thallium stress result",
        optional: true,
        options: [
          [3, "Normal"],
          [6, "Fixed defect"],
          [7, "Reversible defect"],
        ],
      },
    ],
  },
];
export const fields = groups.flatMap((g) => g.fields);
export const labels = Object.fromEntries(fields.map((f) => [f.key, f.label]));
export const empty = Object.fromEntries(fields.map((f) => [f.key, ""]));
export const example = Object.fromEntries(
  fields.map((f, i) => [
    f.key,
    String([63, 1, 4, 145, 233, 1, 2, 150, 1, 2.3, 2, 0, 7][i]),
  ]),
);
export type Contribution = {
  feature: string;
  value: number | null;
  imputed: boolean;
  shap_value: number;
  direction: string;
};
export type Evidence = {
  evidence_id: string;
  text: string;
  cosine_distance: number;
  metadata: {
    source_url: string;
    source: string;
    start_index: number;
    chunk_id: string;
    page?: number;
    page_label?: string;
  };
};
export type Analysis = {
  analysis_id: string;
  status: "complete" | "partial";
  prediction: {
    model: string;
    disease_probability: number;
    base_probability: number;
    contributions: Contribution[];
    top_3_contributors: Contribution[];
  };
  evidence: Evidence[];
  retrieval_query: string;
  synthesis: {
    status: string;
    reason: string | null;
    text: string | null;
    provider: string;
    model: string;
  };
  timings_ms: {
    total: number;
    prediction_and_shap: number;
    retrieval: number;
    synthesis: number;
  };
  limitations: string[];
};
