"""Conservative scope rules for Decatur, Alabama news searches."""
import re
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

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
    # Use News results rather than matching dates as words on ordinary pages.
    clean = re.sub(r"\b(today(?:'s)?|tonight|latest|current)\b", "", query, flags=re.I)
    params = {"q": clean + " local reporting (" + outlets + ")", "tbm": "nws"}
    if re.search(r"\b(today|tonight)\b", query, re.I):
        params["tbs"] = "qdr:d"
    elif re.search(r"\b(latest|current|recent)\b", query, re.I):
        params["tbs"] = "qdr:w"
    return params

def article_time(value, now):
    """Parse publication metadata, not arbitrary dates mentioned in an article."""
    value = str(value or "").strip()
    if not value:
        return None
    relative = re.fullmatch(r"(\d+)\s+(minute|hour|day|week)s?\s+ago", value, re.I)
    if relative:
        amount, unit = relative.groups()
        return now - timedelta(**{unit.lower() + "s": int(amount)})
    if value.lower() in ("just now", "today"):
        return now
    if value.lower() == "yesterday":
        return now - timedelta(days=1)
    for fmt in ("%Y-%m-%d %H:%M:%S UTC", "%b %d, %Y", "%B %d, %Y",
                "%m/%d/%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=timezone.utc if fmt.endswith("UTC") else now.tzinfo)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=now.tzinfo)

def fresh_local_result(result, query, now=None):
    """Require dated evidence for today's/latest news; never relabel archive stories."""
    now = now or datetime.now(ZoneInfo("America/Chicago"))
    if re.search(r"\b(today|tonight)\b", query, re.I):
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif re.search(r"\b(latest|current|recent)\b", query, re.I):
        cutoff = now - timedelta(days=7)
    else:
        return True
    dates = [article_time(result.get(field), now) for field in ("published_at", "date")]
    dates = [date for date in dates if date is not None]
    return bool(dates) and all(cutoff <= date <= now for date in dates)


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
