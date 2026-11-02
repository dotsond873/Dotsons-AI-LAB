"""Server-side SerpApi search with sanitized errors."""
import os
from urllib.parse import urlparse
import httpx


class SearchUnavailable(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


async def search_web(query: str) -> list[dict[str, str]]:
    key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not key:
        raise SearchUnavailable("Web search is not configured. Add SERPAPI_API_KEY to the backend environment.", 503)
    query = query.strip()
    if not query or len(query) > 2000:
        raise SearchUnavailable("Web search needs a query between 1 and 2,000 characters.", 400)
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://serpapi.com/search.json",
                params={"engine": "google", "q": query, "api_key": key, "hl": "en", "gl": "us"},
            )
        if response.status_code in (401, 403):
            raise SearchUnavailable("Web search credentials were rejected. Check SERPAPI_API_KEY.", 503)
        if response.status_code == 429:
            raise SearchUnavailable("Web search quota or rate limit reached. Try again later.", 503)
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException:
        raise SearchUnavailable("Web search timed out. Please try again.", 504) from None
    except (httpx.HTTPError, ValueError):
        raise SearchUnavailable("Web search is temporarily unavailable.") from None
    if not isinstance(data, dict) or data.get("error"):
        raise SearchUnavailable("Web search failed. Check your SerpApi account status.")
    results = data.get("organic_results", [])
    if not isinstance(results, list):
        raise SearchUnavailable("Web search returned an unexpected response.")
    sources = []
    for result in results:
        if not isinstance(result, dict):
            continue
        url = result.get("link")
        if not isinstance(url, str):
            continue
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http") or not parsed.netloc:
            continue
        sources.append({
            "title": str(result.get("title") or url)[:300],
            "url": url,
            "snippet": str(result.get("snippet") or "")[:1500],
        })
        if len(sources) == 5:
            break
    return sources
