from langchain.tools import tool
import requests

from utils.logger import get_logger

_logs = get_logger(__name__)

# TheAudioDB's shared free test key ("2"), no signup required.
SEARCH_URL = "https://www.theaudiodb.com/api/v1/json/2/search.php"


@tool
def get_artist_spotlight(artist: str) -> str:
    """
    Looks up background info for a music artist or band using the free
    TheAudioDB API (no API key required): formation year, genre, style,
    and biography. Use this to build an on-air "Artist Spotlight" segment;
    do not read the raw biography verbatim, rephrase it in the show's voice.
    """
    _logs.debug(f"Looking up artist spotlight for: {artist}")
    response = requests.get(SEARCH_URL, params={"s": artist})
    response.raise_for_status()
    artists = response.json().get("artists")
    if not artists:
        return f"No artist information found for '{artist}'."

    data = artists[0]
    bio = (data.get("strBiographyEN") or "No biography available.").strip()
    # Keep the raw context passed to the model bounded.
    if len(bio) > 1200:
        bio = bio[:1200].rsplit(".", 1)[0] + "."

    info = (
        f"Artist: {data.get('strArtist')}\n"
        f"Formed: {data.get('intFormedYear') or 'unknown'}\n"
        f"Genre: {data.get('strGenre') or 'unknown'}\n"
        f"Style: {data.get('strStyle') or 'unknown'}\n"
        f"Mood: {data.get('strMood') or 'unknown'}\n"
        f"Biography: {bio}"
    )
    _logs.debug(f"Artist spotlight info: {info}")
    return info
