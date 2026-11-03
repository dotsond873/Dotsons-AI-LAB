"""Conservative scope rules for Decatur, Alabama news searches."""
import re
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

OUTLETS = {
    "decatur": ("decaturdaily.com", "whnt.com", "waff.com", "waaytv.com", "rocketcitynow.com"),
    "birmingham": ("al.com", "wbrc.com", "wvtm13.com", "cbs42.com", "abc3340.com", "birminghamtimes.com"),
}

def local_news_city(query):
    if not re.search(r"\b(news|headlines?|stories)\b", query, re.I):
        return None
    if re.search(r"\b(world|national|international)\s+(news|headlines?)\b", query, re.I):
        return None
    match = re.search(r"\b(?:in|from|for|about)\s+([a-z][a-z .'-]{1,45}?),?\s+(?:alabama|al)\b", query, re.I)
    if not match:
        match = re.search(r"^([a-z][a-z .'-]{1,45}?),?\s+(?:alabama|al)\b", query, re.I)
    if not match:
        return None
    city = re.sub(r"^(?:(?:latest|local|current|recent|today's|todays|today)\s+)+", "", match.group(1), flags=re.I)
    return city.strip().lower()

def is_local_news(query):
    return local_news_city(query) is not None

def is_decatur_news(query):
    return local_news_city(query) == "decatur"

def news_search_params(query):
    if not is_local_news(query):
        return {}
    topic = re.split(r"[.!?]", query)[0]
    topic = re.sub(r"\b(today(?:'s|s)?|tonight|latest|current|recent)\b", "", topic, flags=re.I)
    params = {"q": topic.strip(), "tbm": "nws"}
    if re.search(r"\b(today(?:'s|s)?|tonight)\b", query, re.I):
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
    if re.search(r"\b(today(?:'s|s)?|tonight)\b", query, re.I):
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif re.search(r"\b(latest|current|recent)\b", query, re.I):
        cutoff = now - timedelta(days=7)
    else:
        return True
    dates = [article_time(result.get(field), now) for field in ("published_at", "date")]
    dates = [date for date in dates if date is not None]
    return bool(dates) and all(cutoff <= date <= now for date in dates)


def relevant_local_result(result, query="Decatur Alabama news"):
    city = local_news_city(query)
    if not city:
        return True
    parsed = urlparse(str(result.get("link") or ""))
    host = (parsed.hostname or "").lower()
    outlets = OUTLETS.get(city, ())
    if outlets and not any(host == outlet or host.endswith("." + outlet) for outlet in outlets):
        return False
    path = parsed.path.rstrip("/")
    if not path or path.lower() in ("/news", "/news/local", "/local", "/sports", "/" + city):
        return False
    evidence = str(result.get("title") or "") + " " + str(result.get("snippet") or "")
    if re.search(r"\b" + re.escape(city) + r"[, ]+(illinois|georgia|indiana|texas|michigan|england|uk|il|ga|tx|mi)\b", evidence, re.I):
        return False
    names = [city] + (["morgan county"] if city == "decatur" else [])
    return any(re.search(r"\b" + re.escape(name) + r"\b", evidence, re.I) for name in names)
