"""Small deterministic editorial checks; not a replacement for scientific review."""
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
