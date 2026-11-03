"""Keep input bytes below the provider's token allowance."""
import json

MAX_PROMPT_BYTES = 6000

def clip_utf8(text, limit):
    return str(text).encode("utf-8")[:max(0, limit)].decode("utf-8", errors="ignore")

def fit_search_context(context, limit):
    try:
        sources = json.loads(context)
    except (ValueError, TypeError):
        return clip_utf8(context, limit)
    if not isinstance(sources, list):
        return clip_utf8(context, limit)
    sources = [dict(source) for source in sources if isinstance(source, dict)]
    def encoded():
        return json.dumps(sources, ensure_ascii=False, separators=(",", ":"))
    for source in sources:
        if "page_text" in source:
            source["page_text"] = clip_utf8(source["page_text"], 1400)
    if len(encoded().encode("utf-8")) > limit:
        for source in sources:
            source.pop("page_text", None)
            source["snippet"] = clip_utf8(source.get("snippet", ""), 250)
            if source.get("page_status") == "read":
                source["page_status"] = "excerpt_omitted"
    while sources and len(encoded().encode("utf-8")) > limit:
        sources.pop()
    return encoded() if len(encoded().encode("utf-8")) <= limit else ""
