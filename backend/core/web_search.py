"""Server-side SerpApi search with sanitized errors."""
import os
import asyncio
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlparse
import httpx
from core.local_news import is_local_news, news_search_params, relevant_local_result, fresh_local_result


class SearchUnavailable(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def dated_query(query: str, today=None) -> str:
    """Resolve relative dates before searching; preserve explicit years."""
    today = today or datetime.now(ZoneInfo("America/Chicago")).date()
    days = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    def weekday(match):
        target = days.index(match.group(1).lower())
        offset = (target - today.weekday()) % 7 or 7
        return (today + timedelta(days=offset)).strftime("%B %d, %Y")
    # Leave explicit historical dates and bare weekdays unchanged.
    query = re.sub(r"\b(?:next|this)\s+(" + "|".join(days) + r")\b", weekday, query, flags=re.I)
    if not re.search(r"\b20\d{2}\b", query) and not re.search(r"\blast\b", query, re.I):
        query = re.sub(r"\b(" + "|".join(days) + r")\b", weekday, query, flags=re.I)
    for label, offset in (("tomorrow", 1), ("today", 0), ("yesterday", -1)):
        query = re.sub(r"\b" + label + r"\b", (today + timedelta(days=offset)).strftime("%B %d, %Y"), query, flags=re.I)
    if not re.search(r"\b20\d{2}\b", query) and re.search(r"\b(next|current|latest|recent|schedule)\b", query, re.I):
        query += f" {today.year}"
    return query


async def read_page(client, source, key):
    """Read at most two search-result pages through SerpApi, never local URLs."""
    parsed = urlparse(source["url"])
    if parsed.username or parsed.password or not parsed.hostname or "." not in parsed.hostname:
        source["page_status"] = "unavailable"
        return
    try:
        response = await client.get(
            "https://serpapi.com/search.md",
            params={"engine": "extract", "mode": "scrape", "url": source["url"],
                    "api_key": key, "output": "md", "timeout": 10000},
            timeout=12.0,
        )
        response.raise_for_status()
        content = response.text.strip()
        content_type = response.headers.get("content-type", "")
        if not content or "json" in content_type or content.startswith(("{", "<!DOCTYPE", "<html")):
            source["page_status"] = "unavailable"
            return
        source["page_text"] = content[:1800]
        source["page_status"] = "read"
    except (httpx.HTTPError, ValueError):
        source["page_status"] = "unavailable"


async def search_web(query: str) -> list[dict[str, str]]:
    key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not key:
        raise SearchUnavailable("Web search is not configured. Add SERPAPI_API_KEY to the backend environment.", 503)
    query = query.strip()
    if not query or len(query) > 2000:
        raise SearchUnavailable("Web search needs a query between 1 and 2,000 characters.", 400)
    local_news = is_local_news(query)
    params = {"engine": "google", "q": dated_query(query), "api_key": key, "hl": "en", "gl": "us"}
    local_params = news_search_params(query)
    if local_params:
        params.update(local_params)
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://serpapi.com/search.json",
                params=params,
            )
            # Some upstream News requests fail even when ordinary search works.
            # Retry once without tbm; publication-date filtering still applies.
            news_empty = False
            if local_news and response.status_code == 200:
                news_data = response.json()
                if isinstance(news_data, dict):
                    news_error = str(news_data.get("error", ""))
                    news_empty = (not news_error and not news_data.get("news_results")) or bool(
                        re.search(r"(?:hasn.t returned any results|no (?:search )?results (?:were )?found|returned no results)", news_error, re.I)
                    )
            if local_news and (response.status_code not in (200, 401, 403, 429) or news_empty):
                fallback_params = {k: v for k, v in params.items() if k != "tbm"}
                response = await client.get(
                    "https://serpapi.com/search.json", params=fallback_params,
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
    if not isinstance(data, dict):
        raise SearchUnavailable("Web search returned an unexpected response.")
    if data.get("error"):
        error = str(data["error"])
        # An empty Google result set is not a credential or account failure.
        if re.search(r"(?:hasn.t returned any results|no (?:search )?results (?:were )?found|returned no results)", error, re.I):
            return []
        # Expose a bounded explanation, never the credential or full request URL.
        safe_error = error.replace(key, "[redacted]")
        safe_error = re.sub(r"https?://\S+", "[provider URL]", safe_error)
        raise SearchUnavailable("Search provider: " + safe_error[:240])
    results = data.get("news_results", data.get("organic_results", [])) if local_news else data.get("organic_results", [])
    if not isinstance(results, list):
        raise SearchUnavailable("Web search returned an unexpected response.")
    sources = []
    for result in results:
        if not isinstance(result, dict):
            continue
        if local_news and (not relevant_local_result(result, query) or not fresh_local_result(result, query)):
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
            "date": str(result.get("published_at") or result.get("date") or ""),
            "page_status": "not_read",
        })
        if len(sources) == 5:
            break
    async with httpx.AsyncClient(timeout=12.0) as client:
        await asyncio.gather(*(read_page(client, source, key) for source in sources[:2]))
    return sources
