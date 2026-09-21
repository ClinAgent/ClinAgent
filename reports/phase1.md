# Phase 1: Cleveland data audit and model selection

## Decision

Use L2-regularized logistic regression (`C=0.1`) for the current prototype. It had the highest mean development ROC-AUC among the tested configurations and the lowest Brier score. This is a bounded comparison, not proof of a universally optimal model. XGBoost was trained and compared, but was not selected.

## Data inspection

- Source: [UCI Heart Disease, Cleveland subset](https://archive.ics.uci.edu/dataset/45/heart+disease). Only `processed.cleveland.data` is used; other centers are excluded.
- 303 rows, 13 predictors, one target; no exact duplicate records. Original target counts: 0=164, 1=55, 2=36, 3=35, 4=13. Binary target: 164 absent, 139 present (45.9%).
- Missing values: `ca` has 4 and `thal` has 2. No rows are dropped. Numeric fields use training medians; categorical fields use training modes.
- Codes match original UCI definitions, especially `cp=1..4` and `thal=3/6/7`; recoded Kaggle variants are rejected.
- Age, resting blood pressure, cholesterol, maximum heart rate, ST depression, and vessel count are numeric. The other seven fields are categorical and one-hot encoded. Vessel count is treated as a count; slope is categorical to avoid assuming equal spacing.
- Full-data inspection is limited to structural validation, missingness, duplicates and target counts. All distribution and association analysis below uses the development subset.

### Development distributions

| Feature | Minimum | Median | Maximum |
|---|---:|---:|---:|
| age | 29 | 56 | 77 |
| trestbps | 94 | 130 | 200 |
| chol | 126 | 244.5 | 564 |
| thalach | 71 | 153.5 | 202 |
| oldpeak | 0 | 0.8 | 6.2 |
| ca | 0 | 0 | 3 |

Extremes are retained after schema checks: rare high measurements can be clinically real. No outlier clipping, feature removal, oversampling, or synthetic patient generation is used. The small cohort and mixed feature types favor strong regularization and make deep models difficult to justify.

Numeric Spearman associations with the binary label (descriptive, not causal): `age` +0.220, `trestbps` +0.125, `chol` +0.117, `thalach` -0.410, `oldpeak` +0.388, `ca` +0.474. Nominal category codes are not assigned rank correlations; category counts and per-category target rates are recorded in `data_audit.json`.

## Comparison protocol

- Fixed stratified 80/20 split, seed 42: 242 development rows and 61 holdout rows. The holdout is saved, never scored or used to select a model in Phase 1.
- Identical 5-fold stratified cross-validation repeated 3 times (15 folds) for all candidates. Imputation, scaling, and encoding are refit inside every outer training fold.
- CPU-only execution with two native threads; folds run serially. Nine configurations cover six predictive model families plus a dummy baseline. Logistic regression receives three prespecified regularization strengths; this is not an exhaustive or equal-budget hyperparameter search.
- RBF SVM uses sigmoid calibration with three internal folds. Outer validation is excluded from both preprocessing and calibration. Preprocessing is shared within each outer training partition, so inner calibration is not a separate end-to-end validation estimate.
- Primary selection: highest mean ROC-AUC; exact ties use lower Brier score. Threshold metrics use each estimator's default classification rule. No threshold tuning is done.
- Repeated folds overlap, so fold standard deviations are descriptive, not independent confidence intervals. Selection on these folds introduces optimism; final evaluation and uncertainty estimates belong to Phase 5.

| Candidate | ROC-AUC mean ± SD | Brier ↓ | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| logistic_c0.1 | 0.9016 ± 0.0391 | 0.1296 | 0.8320 | 0.8500 | 0.7771 | 0.8086 |
| extra_trees | 0.8931 ± 0.0419 | 0.1348 | 0.8071 | 0.8094 | 0.7652 | 0.7830 |
| logistic_c1 | 0.8924 ± 0.0425 | 0.1315 | 0.8251 | 0.8478 | 0.7652 | 0.7998 |
| random_forest | 0.8910 ± 0.0425 | 0.1351 | 0.8045 | 0.8008 | 0.7711 | 0.7821 |
| logistic_c10 | 0.8865 ± 0.0444 | 0.1360 | 0.8251 | 0.8425 | 0.7711 | 0.8014 |
| xgboost | 0.8827 ± 0.0387 | 0.1387 | 0.8073 | 0.8091 | 0.7711 | 0.7847 |
| rbf_svm | 0.8794 ± 0.0433 | 0.1385 | 0.8115 | 0.8170 | 0.7713 | 0.7887 |
| hist_gradient_boosting | 0.8676 ± 0.0378 | 0.1521 | 0.7906 | 0.7820 | 0.7621 | 0.7674 |
| dummy | 0.5000 ± 0.0000 | 0.2483 | 0.5413 | 0.0000 | 0.0000 | 0.0000 |

Saved model size: 4,938 bytes. Median warm single-patient prediction: 2.46 ms over 30 calls on this machine. These timings exclude SHAP, RAG, cloud inference and HTTP; they do not establish the future end-to-end three-second target.

## Interpretation and limitations

The endpoint is existing angiographic disease presence (`num > 0`), not incident disease or ten-year ASCVD risk. The cohort is small, historical, and drawn from a diagnostic setting. Vessel count, thallium testing, and exercise measurements may not be available during routine primary-prevention intake. A primary-prevention guideline is useful contextual evidence but cannot validate this model or turn its probability into an ASCVD risk score.

The probability is not yet externally validated or established as calibrated for clinical use. Performance differences between leading candidates are small relative to fold variability. Calibration, subgroup performance, transportability, threshold selection and prospective validation remain open. SHAP explains associations learned by the model, not biological causes or treatment effects.

Raw audit and per-fold scores are stored alongside this report. Dataset SHA-256: `a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8`.
