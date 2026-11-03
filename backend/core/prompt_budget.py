"""Keep input bytes below the provider's token allowance."""
import json

MAX_PROMPT_BYTES = 6000
MAX_HISTORY_BYTES = 2400

def fit_history(history, limit):
    """Keep recent complete messages rather than slicing through a transcript."""
    parts = []
    remaining = max(0, min(limit, MAX_HISTORY_BYTES))
    for item in reversed(history[-20:]):
        part = f"\n{item.get('role', 'user').upper()}: {item.get('content', '')}"
        size = len(part.encode("utf-8"))
        if size > remaining:
            # Keep a useful prefix of an oversized newest message with its role.
            if not parts and remaining:
                parts.append(clip_utf8(part, remaining))
            break
        parts.append(part)
        remaining -= size
    return "".join(reversed(parts))

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
