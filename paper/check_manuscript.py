"""Small deterministic editorial checks; not a replacement for scientific review."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
text = (HERE / 'main.tex').read_text()
bib = (HERE / 'references.bib').read_text()
abstract = text.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
assert len(abstract.split()) == 200, len(abstract.split())
terms = text.split(r'\begin{IEEEkeywords}')[1].split(r'\end{IEEEkeywords}')[0]
assert len(terms.split(',')) == 5
assert re.findall(r'\\section\{([^}]+)\}', text) == [
 'Introduction','Related Works','Proposed Methodology',
 'Experimental Results and Discussion','Conclusion and Future Works']
assert r'\bibliography{references}' in text
assert not re.search(r'arxiv|preprint', bib, flags=re.I)
keys = set(re.findall(r'@\w+\{([^,]+),', bib))
cited = {key for group in re.findall(r'\\cite\{([^}]+)\}', text) for key in group.split(',')}
assert cited == keys, (cited-keys, keys-cited)
e = json.loads((HERE.parent / 'reports/evaluation.json').read_text())
assert f"{100*e['ml']['accuracy']:.2f}" in abstract
assert f"{e['ml']['roc_auc']:.4f}" in abstract
assert e['end_to_end']['complete_requests'] == 0
assert json.loads((HERE / 'generated/derived_metrics.json').read_text())['new_retrieval_experiment'] is False
print('PASS: 200-word abstract, five terms, requested headings, published citation keys, numerical claims.')

for name, expected in json.loads((HERE / 'generated/source_checksums.json').read_text()).items():
    assert hashlib.sha256((HERE.parent / name).read_bytes()).hexdigest() == expected, name
print('PASS: report checksums match the manuscript evidence snapshot.')

tn, fp, fn, tp = e['ml']['confusion_matrix_tn_fp_fn_tp']
assert tn + fp + fn + tp == e['ml']['holdout_rows'] == 61
assert abs((tn + tp) / 61 - e['ml']['accuracy']) < 1e-12
assert abs(tp / (tp + fp) - e['ml']['precision']) < 1e-12
assert abs(tp / (tp + fn) - e['ml']['recall']) < 1e-12
assert abs(2 * tp / (2 * tp + fp + fn) - e['ml']['f1']) < 1e-12
for name in ['model-comparison', 'holdout-performance', 'retrieval-quality',
             'partial-latency', 'local-shap']:
    assert f'figures/results/{name}.pdf' in text
    assert (HERE / f'figures/results/{name}.pdf').stat().st_size > 1000
assert 'OpenRouter' in text and 'a9b2ac7' in text
print('PASS: plotted holdout counts agree with metrics; five result figures are embedded.')
