"""Conservative scope rules for Decatur, Alabama news searches."""
import re
from urllib.parse import urlparse

LOCAL_OUTLETS = ("decaturdaily.com", "whnt.com", "waff.com", "waaytv.com", "rocketcitynow.com")

def is_decatur_news(query):
    return bool(re.search(r"\bdecatur\b", query, re.I)
                and re.search(r"\b(alabama|al)\b", query, re.I)
                and re.search(r"\b(news|headlines?|stories)\b", query, re.I)
                and not re.search(r"\b(world|national|international)\s+(news|headlines?)\b", query, re.I))

def news_search_params(query):
    if not is_decatur_news(query):
        return {}
    outlets = " OR ".join("site:" + host for host in LOCAL_OUTLETS)
    params = {"q": query + " local reporting (" + outlets + ")"}
    if re.search(r"\b(today|latest|current|tonight)\b", query, re.I):
        params["tbs"] = "qdr:d"
    return params

def relevant_local_result(result):
    title = str(result.get("title") or "")
    snippet = str(result.get("snippet") or "")
    url = str(result.get("link") or "")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not any(host == outlet or host.endswith("." + outlet) for outlet in LOCAL_OUTLETS):
        return False
    # A newspaper homepage includes unrelated wire stories; require an article.
    path = parsed.path.rstrip("/")
    if not path or path.lower() in ("/news", "/news/local", "/local", "/sports"):
        return False
    evidence = title + " " + snippet
    if re.search(r"\bdecatur[, ]+(illinois|georgia|indiana|texas|il|ga|in|tx)\b", evidence, re.I):
        return False
    return bool(re.search(r"\b(decatur|morgan county)\b", evidence, re.I))
