"""Decide when fresh web evidence is useful; explicit choices always win."""
import re
from datetime import datetime
from zoneinfo import ZoneInfo


def should_search(message: str, preference: bool | None = None) -> bool:
    if preference is not None:
        return preference
    text = message.lower().replace("’", "'")
    if re.search(r"\b(don't|do not|without)\s+(?:use\s+)?(?:the\s+)?(?:web|internet|brows(?:e|ing)|search)", text):
        return False
    if re.match(r"\s*(what (?:is|are) (?:an? |the )?|explain )", text) and re.search(r"\b(exchange rate|stock price)\??$", text):
        return False
    if re.match(r"\s*(rewrite|summarize|proofread|translate)\b", text) and re.search(r"\b(pasted|above|following|this text)\b", text):
        return False
    # Writing, translation and explanations do not need paid searches by default.
    if re.match(r"\s*(write|rewrite|draft|translate|summarize|proofread|imagine)\b", text) and not re.search(r"\b(latest|today|current|news|look up|search|verify)\b", text):
        return False
    if re.search(r"\b(search (?:the web|online|for)|look up|browse|fact.check|verify|sources?|citations?)\b|https?://", text):
        return True
    if re.search(r"\b(news|headlines?|weather|forecast|stock price|exchange rate|election results?|outages?|breaking)\b", text):
        return True
    if re.search(r"\b(today(?:'s)?|tonight|tomorrow|yesterday|latest|currently|right now|up.to.date|this (?:week|month|year)|next (?:week|weekend|monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", text):
        return True
    if re.search(r"\b(price[sd]?|costs?|hours|schedule|standings|scores?|kickoff|availability|in stock|who (?:is|does|won|plays)|president|ceo)\b", text):
        # Exclude common timeless explanatory questions.
        return not bool(re.match(r"\s*(what (?:is|are)|explain|how (?:does|do))\b", text) and re.search(r"\b(work|mean|definition|stock price|exchange rate|president|ceo)\b", text))
    year = datetime.now(ZoneInfo("America/Chicago")).year
    return any(int(y) >= year for y in re.findall(r"\b(20\d{2})\b", text))
