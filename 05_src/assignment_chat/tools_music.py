from pathlib import Path

from langchain.tools import tool
import chromadb
from pydantic import BaseModel, Field

from assignment_chat.clients import get_embedding_function
from utils.logger import get_logger

_logs = get_logger(__name__)

STORE_PATH = Path(__file__).parent / "chroma_store"
COLLECTION_NAME = "pitchfork_reviews"

_collection = None


def _get_collection():
    # Lazily initialized so the gateway/API key env vars (loaded by
    # main.py/app.py at startup) are available by the time this actually
    # needs them, regardless of module import order.
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(STORE_PATH))
        _collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
        )
    return _collection


class AlbumRecommendation(BaseModel):
    """A single album recommendation pulled from the show's record crate."""

    title: str = Field(..., description="The title of the album.")
    artist: str = Field(..., description="The artist of the album.")
    year: int | None = Field(None, description="The release year of the album.")
    genre: str | None = Field(None, description="The album's genre.")
    score: float | None = Field(
        None,
        description="Pitchfork score, 0-10. Above 8.0 is a must-listen; above 6.5 is good.",
    )
    review_excerpt: str = Field(..., description="A relevant excerpt from the album's review.")


@tool
def search_record_crate(query: str, n_results: int = 3) -> list[AlbumRecommendation]:
    """
    Searches the show's record crate - a semantic index of Pitchfork
    album reviews - for albums matching a mood, genre, artist, or theme
    the listener describes. Returns up to n_results recommendations.
    """
    _logs.debug(f"Searching record crate for: {query!r} (n_results={n_results})")
    results = _get_collection().query(query_texts=[query], n_results=n_results)

    recommendations = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    for doc_id, document, metadata in zip(ids, documents, metadatas):
        recommendations.append(
            AlbumRecommendation(
                title=metadata.get("album", "N/A"),
                artist=metadata.get("artist", "N/A"),
                year=metadata.get("year"),
                genre=metadata.get("genre"),
                score=metadata.get("score"),
                review_excerpt=document[:500],
            )
        )
    _logs.debug(f"Record crate results: {recommendations}")
    return recommendations
