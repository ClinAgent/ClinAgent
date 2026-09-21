"""Small, CPU-only encoder. This is an embedding model, not a local generative LLM."""

import os

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# Explicit revision prevents an upstream model update from silently mixing vector spaces.
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def make_embeddings(*, offline=False):
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    import torch
    from langchain_huggingface import HuggingFaceEmbeddings

    torch.set_num_threads(2)
    return HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        cache_folder="artifacts/embedding_cache",
        model_kwargs={
            "device": "cpu",
            "revision": MODEL_REVISION,
            "local_files_only": offline,
            "trust_remote_code": False,
        },
        encode_kwargs={"batch_size": 16, "normalize_embeddings": True},
        show_progress=False,
    )
