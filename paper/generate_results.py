"""Regenerate manuscript tables from committed evaluation reports (no retraining)."""
import hashlib
import json
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / 'generated'
OUT.mkdir(exist_ok=True)
load = lambda name: json.loads((ROOT / 'reports' / name).read_text())
comparison = load('model_comparison.json')
evaluation = load('evaluation.json')
labels = {'logistic_c0.1': 'Logistic ($C=0.1$)', 'logistic_c1': 'Logistic ($C=1$)',
          'logistic_c10': 'Logistic ($C=10$)', 'extra_trees': 'Extra trees',
          'random_forest': 'Random forest', 'hist_gradient_boosting': 'Histogram boosting',
          'xgboost': 'XGBoost', 'rbf_svm': 'Calibrated RBF SVM', 'dummy': 'Prior-only dummy'}

def table(name, caption, label, columns, header, rows):
    text = ('\\begin{table}[t]\n\\centering\n\\caption{' + caption + '}\n\\label{' + label + '}\n'
            '\\small\n\\begin{tabular}{' + columns + '}\n\\toprule\n' + header + r' \\' + '\n\\midrule\n')
    text += '\n'.join(' & '.join(row) + r' \\' for row in rows)
    text += '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n'
    (OUT / name).write_text(text)

table('model-table.tex', 'Development comparison: mean over 15 folds; AUC standard deviation in parentheses.',
      'tab:models', 'lrr', r'Model & ROC-AUC (SD) & Brier',
      [[labels[r['model']], f"{r['auc']:.4f} ({r['auc_std']:.4f})", f"{r['brier']:.4f}"]
       for r in comparison['candidates']])
m = evaluation['ml']
table('holdout-table.tex', 'Held-out performance of the selected logistic model ($n=61$).',
      'tab:holdout', 'lr', 'Metric & Value',
      [[label, f"{m[key]:.4f}"] for label, key in [('Accuracy','accuracy'),('Precision','precision'),
       ('Recall','recall'),('F1-score','f1'),('ROC-AUC','roc_auc'),('Brier score','brier')]])
topics = {'activity':'Physical activity', 'aspirin_age':'Aspirin: age over 70',
          'aspirin_bleeding':'Aspirin: bleeding risk', 'diet':'Dietary pattern',
          'obesity':'Obesity / weight loss', 'ldl':'LDL-C $\\geq190$ mg/dL'}
rows, recalls, precisions, details = [], [], [], []
for q in evaluation['rag']['queries']:
    relevant = set(q['relevant_chunk_ids'])
    retrieved = set(q['retrieved_chunk_ids'][:2])
    hits = len(relevant & retrieved)
    precision, recall = hits / 2, hits / len(relevant)
    assert abs(precision - q['precision_at_2']) < 1e-12
    recalls.append(recall); precisions.append(precision)
    rows.append([topics[q['id']], str(len(relevant)), f'{precision:.4f}', f'{recall:.4f}'])
    details.append({'id':q['id'], 'hits':hits, 'labeled_relevant':len(relevant), 'recall_at_2':recall})
rows.append(['Mean', '--', f'{mean(precisions):.4f}', f'{mean(recalls):.4f}'])
table('retrieval-table.tex', 'Development retrieval diagnostic. Recall is relative to the recorded seed labels.',
      'tab:retrieval','lrrr',r'Topic & $|G|$ & P@2 & R@2',rows)
assert abs(mean(precisions)-evaluation['rag']['mean_precision_at_2']) < 1e-12
(OUT / 'derived_metrics.json').write_text(json.dumps({
 'source':'reports/evaluation.json', 'new_retrieval_experiment':False,
 'mean_seed_recall_at_2':mean(recalls), 'queries':details,
 'partial_http_median_ms':1000*median(s['seconds'] for s in evaluation['end_to_end']['samples']),
 'complete_requests':evaluation['end_to_end']['complete_requests']},indent=2)+'\n')

source_paths = ['reports/data_audit.json', 'reports/model_comparison.json',
                'reports/evaluation.json', 'reports/example_explanation.json',
                'evaluation/retrieval_labels.json']
(OUT / 'source_checksums.json').write_text(json.dumps({
    p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in source_paths
}, indent=2) + '\n')
