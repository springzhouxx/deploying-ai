"""
Builds the "Crate Digger" vector store: a small, file-persisted ChromaDB
collection of Pitchfork album reviews. The output, ./chroma_store, is
already committed to the repo, so this is a one-time offline script.

Running it again requires a local source data file that is not included
in this repo - see readme.md for details.
"""
import json
import os
import random
import shutil
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".secrets")

import chromadb

from assignment_chat.clients import get_embedding_function

HERE = Path(__file__).parent
SOURCE_PATH = HERE / ".." / "documents" / "pitchfork" / "chroma_inputs.jsonl"
STORE_PATH = HERE / "chroma_store"
COLLECTION_NAME = "pitchfork_reviews"
SAMPLE_SIZE = int(os.getenv("SAMPLE_SIZE", "1400"))  # keeps chroma_store/ under the 40MB repo limit
SEED = 42
BATCH_SIZE = 500


def iter_records(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def reservoir_sample(path: Path, k: int, seed: int = SEED) -> list[dict]:
    """
    Streams the source file once and returns a uniform random sample of
    size k, deduplicated by id (the source file has ~700 duplicate rows).
    """
    rng = random.Random(seed)
    sample: list[dict] = []
    seen_ids: set[str] = set()
    n_seen = 0
    for record in iter_records(path):
        if record["id"] in seen_ids:
            continue
        seen_ids.add(record["id"])
        if n_seen < k:
            sample.append(record)
        else:
            j = rng.randint(0, n_seen)
            if j < k:
                sample[j] = record
        n_seen += 1
    return sample


def clean_metadata(metadata: dict) -> dict:
    # Chroma metadata values must be str/int/float/bool - drop None fields.
    return {k: v for k, v in metadata.items() if v is not None}


def build_store(sample_size: int = SAMPLE_SIZE, store_path: Path = STORE_PATH) -> "chromadb.Collection":
    if store_path.exists():
        shutil.rmtree(store_path)

    records = reservoir_sample(SOURCE_PATH, sample_size)

    client = chromadb.PersistentClient(path=str(store_path))
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )

    for i in range(0, len(records), BATCH_SIZE):
        chunk = records[i : i + BATCH_SIZE]
        collection.add(
            ids=[r["id"] for r in chunk],
            embeddings=[r["embedding"] for r in chunk],
            documents=[r["text"] for r in chunk],
            metadatas=[clean_metadata(r["metadata"]) for r in chunk],
        )

    return collection


def dir_size_mb(path: Path) -> float:
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024)


if __name__ == "__main__":
    collection = build_store()
    size_mb = dir_size_mb(STORE_PATH)
    print(f"Built collection '{COLLECTION_NAME}' with {collection.count()} records at {STORE_PATH}")
    print(f"Store size on disk: {size_mb:.2f} MB")
