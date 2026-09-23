"""Plot saved experiments only; never rerun models or invent ROC coordinates."""
import json
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/figures/results"
OUT.mkdir(parents=True, exist_ok=True)
read = lambda name: json.loads((ROOT / "reports" / name).read_text())
evaluation = read("evaluation.json")
comparison = read("model_comparison.json")
explanation = read("example_explanation.json")
BLUE, GRAY, ORANGE = "#0073AE", "#64717D", "#A45425"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 8,
                     "pdf.fonttype": 42, "savefig.dpi": 300})

def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=.04)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", pad_inches=.04)
    plt.close(fig)

labels = {"logistic_c0.1": "Logistic C=0.1", "logistic_c1": "Logistic C=1",
          "logistic_c10": "Logistic C=10", "extra_trees": "Extra trees",
          "random_forest": "Random forest", "hist_gradient_boosting": "Histogram boosting",
          "xgboost": "XGBoost", "rbf_svm": "Calibrated RBF SVM", "dummy": "Prior-only dummy"}
rows = comparison["candidates"]
fig, ax = plt.subplots(figsize=(3.6, 2.9), layout="constrained")
for i, r in enumerate(rows):
    ax.errorbar(r["auc"], i, xerr=r["auc_std"], fmt="o", markersize=4,
                capsize=3, color=BLUE if i == 0 else GRAY)
ax.set(yticks=range(len(rows)), yticklabels=[labels[r["model"]] for r in rows],
       xlim=(.45, 1.0), xlabel="Development ROC-AUC (mean ± fold SD)")
ax.invert_yaxis(); ax.grid(axis="x", alpha=.2)
save(fig, "model-comparison")

ml = evaluation["ml"]
fig, axes = plt.subplots(1, 2, figsize=(7, 2.6), layout="constrained", gridspec_kw={"width_ratios": [1.2, 1]})
ax = axes[0]
keys = ["accuracy", "precision", "recall", "f1", "roc_auc"]
ax.barh(range(5), [ml[k] for k in keys], color=BLUE, height=.55)
ax.set(yticks=range(5), yticklabels=["Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC"],
       xlim=(0, 1.13), xticks=[0,.25,.5,.75,1], xlabel="Score", title="(a) Held-out performance")
ax.invert_yaxis()
for i,k in enumerate(keys): ax.text(ml[k]+.018, i, f"{ml[k]:.4f}", va="center", fontsize=8)
tn, fp, fn, tp = ml["confusion_matrix_tn_fp_fn_tp"]
ax = axes[1]; cm = np.array([[tn, fp], [fn, tp]])
ax.imshow(cm, cmap="Blues", vmin=0, vmax=33)
for i in range(2):
    for j in range(2): ax.text(j, i, str(cm[i,j]), ha="center", va="center", fontsize=15, color="white" if cm[i,j]>16 else "black")
ax.set(xticks=[0,1], yticks=[0,1], xticklabels=["Absent", "Present"], yticklabels=["Absent", "Present"],
       xlabel="Predicted disease", ylabel="Observed disease", title="(b) Confusion matrix (n=61)")
save(fig, "holdout-performance")

queries = evaluation["rag"]["queries"]
topics = ["Physical activity", "Aspirin: age >70", "Aspirin: bleeding", "Dietary pattern", "Obesity", "LDL-C ≥190"]
precision, recall = [], []
for q in queries:
    relevant = set(q["relevant_chunk_ids"])
    hits = len(relevant & set(q["retrieved_chunk_ids"][:2]))
    precision.append(hits/2); recall.append(hits/len(relevant))
fig, ax = plt.subplots(figsize=(3.6, 2.9), layout="constrained")
y=np.arange(6)
ax.barh(y-.17,precision,.32,label="Precision@2",color=BLUE)
ax.barh(y+.17,recall,.32,label="Seed-label Recall@2",color=GRAY,hatch="//")
for i,(p,r) in enumerate(zip(precision,recall)):
    if p==r==0: ax.text(.025,i,"No labeled hits",va="center",fontsize=7)
ax.set(yticks=y, yticklabels=topics, xlim=(0,1.06), xlabel="Score (six development queries)")
ax.invert_yaxis(); ax.legend(loc="lower center", bbox_to_anchor=(.5,1), frameon=False, fontsize=7)
save(fig,"retrieval-quality")

names={"age":"Age", "sex":"Sex", "cp":"Chest-pain type", "trestbps":"Resting blood pressure",
       "chol":"Total cholesterol", "fbs":"Fasting glucose flag", "restecg":"Resting ECG", "thalach":"Maximum heart rate",
       "exang":"Exercise-induced angina", "oldpeak":"ST depression", "slope":"ST slope", "ca":"Major vessels", "thal":"Thallium result"}
rows=sorted(explanation["contributions"], key=lambda r:abs(r["shap_value"]), reverse=True)
assert abs(explanation["base_probability"]+sum(r["shap_value"] for r in rows)-explanation["disease_probability"])<1e-6
fig, ax=plt.subplots(figsize=(3.6,3.5),layout="constrained")
values=[100*r["shap_value"] for r in rows]
ax.barh(range(13), values, color=[BLUE if v>=0 else ORANGE for v in values])
ax.set(yticks=range(13),yticklabels=[names[r["feature"]] for r in rows],xlabel="SHAP contribution (percentage points)")
ax.invert_yaxis(); ax.axvline(0,color="black",lw=.6)
save(fig,"local-shap")

samples=evaluation["end_to_end"]["samples"]
assert all(not s["complete"] and s["synthesis_reason"]=="provider_not_configured" for s in samples)
times=[s["seconds"]*1000 for s in samples]
fig,ax=plt.subplots(figsize=(3.6,2.4),layout="constrained")
ax.scatter(range(1,11),times,color=BLUE,zorder=3)
ax.axhline(median(times),color=GRAY,ls="--",label=f"Median {median(times):.2f} ms")
ax.set(xlabel="Recorded request",ylabel="Local HTTP response time (ms)",ylim=(0,100),xticks=range(1,11))
ax.legend(frameon=False,fontsize=7); ax.grid(axis="y",alpha=.2)
save(fig,"partial-latency")
print("Generated five figures from saved reports; no new experiments.")
