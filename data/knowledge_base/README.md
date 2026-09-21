# Phase 2 guideline input

Download the **2019 ACC/AHA Guideline on the Primary Prevention of Cardiovascular
Disease: Executive Summary** from the [AHA/ACC publication](https://www.ahajournals.org/doi/10.1161/CIR.0000000000000677).
Save its text or PDF here as `acc_aha_2019_executive_summary.txt` or
`acc_aha_2019_executive_summary.pdf`. Use the actual article, not a login page,
abstract-only export, or website navigation. Keep the title, DOI, section headings,
and page numbers where available so retrieved passages can be traced to their source.

The Executive Summary is now saved locally as `acc_aha_2019_executive_summary.txt`.
It is an unmodified UTF-8 text/Markdown extraction of the official PDF, obtained
through Firecrawl after the direct PDF download returned HTTP 403. Unlike the
HTML export, this extraction contains the recommendation tables. The adjacent
`acc_aha_2019_source.json` records the retrieval URL, time, method and checksum.
PDF extraction can affect column order, tables and equations; use the linked
original to verify consequential details.

The complete document is kept on disk. Ingestion excludes text from the
References/staff heading onward, publication front matter, and heading-only
chunks from the searchable index. For the downloaded text, the preamble and
methodology are excluded using section boundaries while preserving source offsets. No guideline text is committed to Git. Source identity checks are basic
screening, not an authenticity or completeness guarantee.

The user-added `heart+disease/` folder contains the UCI tabular dataset and is
left intact. Its Cleveland file has the same checksum as the Phase 1 dataset.
It is not ingested as clinical evidence.

The supplied DOI ending in `0678` is the full guideline. The companion Executive
Summary requested in the project brief has DOI ending in `0677`.
