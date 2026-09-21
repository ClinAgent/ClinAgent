"""Real persisted Chroma with a deterministic tiny encoder; semantic smoke tested separately."""

import json

import pytest

pytest.importorskip("langchain_chroma")
from langchain_core.embeddings import Embeddings

from aegishealth.rag.store import GuidelineRetriever, ingest

HEADER = "2019 ACC/AHA Guideline on the Primary Prevention of Cardiovascular Disease: Executive Summary\n"


class TinyEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text):
        return [
            float(text.lower().count(term)) + 0.01
            for term in ["cholesterol", "exercise", "tobacco"]
        ]


@pytest.fixture
def indexed(tmp_path):
    source = tmp_path / "guideline.txt"
    source.write_text(
        HEADER
        + "\n\n".join(
            word * 70
            for word in ["Cholesterol assessment. ", "Exercise activity. ", "Tobacco cessation. "]
        )
    )
    directory = tmp_path / "chroma"
    manifest = ingest(source, directory, embeddings=TinyEmbeddings())
    return source, directory, manifest


def test_persistence_exact_snippets_and_idempotency(indexed):
    source, directory, manifest = indexed
    again = ingest(source, directory, embeddings=TinyEmbeddings())
    assert again["status"] == "unchanged"
    assert again["collection"] == manifest["collection"]
    retriever = GuidelineRetriever(directory, embeddings=TinyEmbeddings())
    snippets = retriever.retrieve("cholesterol")
    assert len(snippets) == 2
    assert snippets[0]["cosine_distance"] <= snippets[1]["cosine_distance"]
    for snippet in snippets:
        start = snippet["metadata"]["start_index"]
        assert source.read_text()[start : start + len(snippet["text"])] == snippet["text"]
        assert "Cholesterol" in snippet["text"]


def test_failed_update_preserves_old_index(indexed):
    source, directory, original = indexed
    source.write_text(source.read_text() + "\nUpdated material.")

    class Broken(TinyEmbeddings):
        def embed_documents(self, texts):
            raise RuntimeError("simulated encoder failure")

    with pytest.raises(RuntimeError, match="simulated"):
        ingest(source, directory, embeddings=Broken())
    assert (
        json.loads((directory / "manifest.json").read_text())["collection"]
        == original["collection"]
    )
    assert not (directory / "ingest.lock").exists()
    assert len(GuidelineRetriever(directory, embeddings=TinyEmbeddings()).retrieve("exercise")) == 2
    updated = ingest(source, directory, embeddings=TinyEmbeddings())
    assert updated["collection"] != original["collection"]


def test_rejects_invalid_query_and_missing_index(indexed, tmp_path):
    _, directory, _ = indexed
    retriever = GuidelineRetriever(directory, embeddings=TinyEmbeddings())
    for query in ["", "  ", None, "a" * 1001]:
        with pytest.raises(ValueError):
            retriever.retrieve(query)
    with pytest.raises(FileNotFoundError, match="No completed"):
        GuidelineRetriever(tmp_path / "missing", embeddings=TinyEmbeddings())


def test_active_ingest_lock_is_respected(indexed):
    source, directory, _ = indexed
    (directory / "ingest.lock").touch()
    with pytest.raises(RuntimeError, match="locked"):
        ingest(source, directory, embeddings=TinyEmbeddings())
    assert (directory / "ingest.lock").exists()
