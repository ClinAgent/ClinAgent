"""Offline ingestion checks; no remote downloads or real clinical text needed."""

from pathlib import Path

import pytest

pytest.importorskip("langchain_text_splitters")
from aegishealth.rag.documents import load_guideline, split_guideline

HEADER = "2019 ACC/AHA Guideline on the Primary Prevention of Cardiovascular Disease: Executive Summary\n"


@pytest.fixture
def guideline(tmp_path):
    path = tmp_path / "guideline.txt"
    path.write_text(
        HEADER + ("Exercise, smoking cessation and blood cholesterol assessment. " * 60)
    )
    return path


def test_chunks_are_exact_source_slices(guideline):
    docs, provenance = load_guideline(guideline)
    chunks = split_guideline(docs)
    assert provenance["source"] == guideline.name
    assert len(chunks) > 2
    assert len({c.metadata["chunk_id"] for c in chunks}) == len(chunks)
    for chunk in chunks:
        start = chunk.metadata["start_index"]
        assert 0 < len(chunk.page_content) <= 500
        assert docs[0].page_content[start : start + len(chunk.page_content)] == chunk.page_content
        assert chunk.metadata["source_url"].endswith("0677")
        assert "page" not in chunk.metadata  # never invent pagination for TXT
    assert split_guideline(docs) == chunks


@pytest.mark.parametrize(
    "suffix,text",
    [
        (".data", "tabular"),
        (".txt", "abstract"),
        (".txt", "<html>Sign in</html>" * 200),
        (".txt", "Wrong document " * 300),
    ],
)
def test_rejects_wrong_or_incomplete_documents(tmp_path, suffix, text):
    path = tmp_path / ("input" + suffix)
    path.write_text(text)
    with pytest.raises(ValueError):
        load_guideline(path)


def test_missing_source():
    with pytest.raises(FileNotFoundError, match="Executive Summary"):
        load_guideline(Path("nonexistent-guideline.pdf"))


def test_scanned_pdf_requires_ocr(tmp_path):
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=600, height=800)
    path = tmp_path / "scan.pdf"
    writer.write(path)
    with pytest.raises(ValueError, match="OCR"):
        load_guideline(path)


def test_excludes_bibliography_and_standalone_headers(guideline):
    original = guideline.read_text()
    guideline.write_text(original + "\n## REFERENCES\nUnrelated citation " * 20)
    docs, _ = load_guideline(guideline)
    assert "Unrelated citation" not in docs[-1].page_content
    from langchain_core.documents import Document

    header = Document(
        page_content="| Recommendations for Adults With High Blood Cholesterol |\n| --- | --- |\n| COR | LOE | Recommendations |",
        metadata=docs[0].metadata,
    )
    chunks = split_guideline([header, *docs])
    assert not any(c.page_content == header.page_content for c in chunks)


def test_front_matter_is_removed_without_losing_source_offsets(guideline):
    original = guideline.read_text()
    text = (
        HEADER
        + "\nAffiliation information.\n## TOP 10 TAKE-HOME MESSAGES\n"
        + original
        + "\n## ACC/AHA TASK FORCE MEMBERS\nStaff information."
    )
    guideline.write_text(text)
    docs, _ = load_guideline(guideline)
    chunks = split_guideline(docs)
    for chunk in chunks:
        offset = chunk.metadata["start_index"]
        assert text[offset : offset + len(chunk.page_content)] == chunk.page_content
        assert "Affiliation information" not in chunk.page_content
        assert "Staff information" not in chunk.page_content


def test_methodology_is_not_retrieved_as_clinical_evidence(guideline):
    text = (
        guideline.read_text()
        + "\n## PREAMBLE\nNonclinical methodology.\n# 2. OVERARCHING\n"
        + ("Patient-centered assessment and evidence. " * 80)
    )
    guideline.write_text(text)
    documents, _ = load_guideline(guideline)
    for chunk in split_guideline(documents):
        offset = chunk.metadata["start_index"]
        assert text[offset : offset + len(chunk.page_content)] == chunk.page_content
        assert "Nonclinical methodology" not in chunk.page_content
