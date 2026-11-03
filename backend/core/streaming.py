"""NDJSON answer events, with memory saved only after successful completion."""
import json
from contextlib import aclosing
from datetime import datetime, timezone

def event(data):
    return json.dumps(data, ensure_ascii=False) + "\n"

async def answer_events(provider, prompt, request, capability, sources, search_status, memory):
    # Page excerpts are model context, not useful stream metadata.
    public_sources = [{key: value for key, value in source.items() if key != "page_text"} for source in sources]
    yield event({"type":"meta", "capability":capability, "sources":public_sources, "search_status":search_status})
    parts = []
    try:
        async with aclosing(provider.stream(prompt)) as stream:
            async for text in stream:
                if text:
                    parts.append(text)
                    yield event({"type":"delta", "text":text})
        answer = "".join(parts)
        if not answer.strip():
            raise ValueError("Empty answer")
        memory.add_message(request.session_id, "user", request.message)
        memory.add_message(request.session_id, "assistant", answer)
        yield event({"type":"done", "session_id":request.session_id, "model":provider.model,
                     "timestamp":datetime.now(timezone.utc).isoformat()})
    except Exception:
        # Never expose upstream request details or credentials through a stream.
        yield event({"type":"error", "message":"Shady's response was interrupted. Please try again."})
