"""Versioned persistent Chroma indexes with an atomic active-index manifest."""

import hashlib
import json
import os
import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from aegishealth.rag.documents import CHUNK_OVERLAP, CHUNK_SIZE, load_guideline, split_guideline
from aegishealth.rag.embeddings import MODEL_NAME, MODEL_REVISION, make_embeddings

DEFAULT_INDEX = Path("artifacts/chroma")
SCHEMA_VERSION = 4


def _client(directory):
    return chromadb.PersistentClient(
        path=str(directory), settings=Settings(anonymized_telemetry=False)
    )


def _manifest(directory):
    path = Path(directory) / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(
            "No completed guideline index. Run: python -m aegishealth.rag ingest --source FILE"
        )
    manifest = json.loads(path.read_text())
    if (
        manifest["schema_version"] != SCHEMA_VERSION
        or manifest["embedding_model"] != MODEL_NAME
        or manifest["embedding_revision"] != MODEL_REVISION
    ):
        raise ValueError("Index configuration changed; rebuild the guideline index")
    return manifest


def ingest(source, directory=DEFAULT_INDEX, *, embeddings=None, offline=False):
    """Re-index a changed source without exposing a partially built collection.

    Only one ingestion process may own the directory at a time. Lock files are
    removed on ordinary failures; after a killed process, remove the stale lock
    only after confirming no writer is running.
    """
    documents, provenance = load_guideline(Path(source))
    chunks = split_guideline(documents)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "ingest.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise RuntimeError(f"Index is locked: {lock}. Another ingestion may be running.") from error
    os.close(fd)
    try:
        config = {
            "schema_version": SCHEMA_VERSION,
            "embedding_model": MODEL_NAME,
            "embedding_revision": MODEL_REVISION,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "distance_metric": "cosine",
            "hnsw_threads": 2,
            **provenance,
        }
        fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
        client = _client(directory)
        if (directory / "manifest.json").exists():
            current = json.loads((directory / "manifest.json").read_text())
            if current["fingerprint"] == fingerprint:
                collection = client.get_collection(current["collection"], embedding_function=None)
                if collection.count() != current["chunk_count"]:
                    raise ValueError("Index is incomplete; use a new index directory to rebuild")
                return {**current, "status": "unchanged"}
        encoder = embeddings if embeddings is not None else make_embeddings(offline=offline)
        collection_name = "guideline_" + uuid.uuid4().hex
        store = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=encoder,
            collection_configuration={"hnsw": {"space": "cosine", "num_threads": 2}},
        )
        temporary = directory / f"manifest.{collection_name}.tmp"
        try:
            for start in range(0, len(chunks), 64):
                batch = chunks[start : start + 64]
                store.add_documents(batch, ids=[d.metadata["chunk_id"] for d in batch])
            count = client.get_collection(collection_name, embedding_function=None).count()
            if count != len(chunks):
                raise RuntimeError("Not all guideline chunks were persisted")
            manifest = {
                **config,
                "fingerprint": fingerprint,
                "collection": collection_name,
                "chunk_count": count,
            }
            temporary.write_text(json.dumps(manifest, indent=2) + "\n")
            temporary.replace(directory / "manifest.json")
        except BaseException:
            temporary.unlink(missing_ok=True)
            client.delete_collection(collection_name)
            raise
        # Retain prior versions so readers holding an older manifest can finish safely.
        return {**manifest, "status": "created"}
    finally:
        lock.unlink(missing_ok=True)


class GuidelineRetriever:
    """Reuse one CPU embedding model and one Chroma client across requests."""

    def __init__(self, directory=DEFAULT_INDEX, *, embeddings=None, offline=False):
        self.manifest = _manifest(directory)
        client = _client(directory)
        collection = client.get_collection(self.manifest["collection"], embedding_function=None)
        if collection.count() != self.manifest["chunk_count"] or collection.count() < 2:
            raise ValueError("Index is empty or incomplete; rebuild before retrieval")
        encoder = embeddings if embeddings is not None else make_embeddings(offline=offline)
        self.store = Chroma(
            client=client,
            collection_name=self.manifest["collection"],
            embedding_function=encoder,
            create_collection_if_not_exists=False,
        )

    def retrieve(self, query: str) -> list[dict]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Clinical query must be a nonempty string")
        if len(query) > 1000:
            raise ValueError("Clinical query must contain at most 1000 characters")
        matches = self.store.similarity_search_with_score(query.strip(), k=2)
        return [
            {
                "rank": rank,
                "text": doc.page_content,
                "metadata": doc.metadata,
                "cosine_distance": float(distance),
            }
            for rank, (doc, distance) in enumerate(matches, start=1)
        ]
