import re
from collections.abc import Iterator

import feedparser
import httpx
import trafilatura

from .config import settings
from .schemas import Article

TAG = re.compile(r"<[^>]+>")


def _entry_text(e) -> str:
    """Prefer the full article body when the feed provides it (content:encoded), else the summary."""
    parts = [e.get("summary", "")]
    if e.get("content"):
        parts.append(e["content"][0].get("value", ""))
    return " ".join(TAG.sub(" ", max(parts, key=len)).split())


def fetch_entries(limit: int) -> Iterator[Article]:
    """Yield lightweight articles, alternating between feeds so one feed doesn't use the whole limit."""
    feeds = [feedparser.parse(u).entries for u in settings.feeds]
    count = 0
    for i in range(max((len(f) for f in feeds), default=0)):
        for entries in feeds:
            if i < len(entries) and count < limit:
                e = entries[i]
                yield Article(
                    url=e.get("link", ""),
                    title=e.get("title", ""),
                    published=e.get("published", ""),
                    text=_entry_text(e),
                )
                count += 1


def load_text(article: Article) -> Article:
    """Try to fetch the full article text; fall back to the RSS text and say why in the logs."""
    try:
        r = httpx.get(article.url, follow_redirects=True, timeout=15,
                      headers={"User-Agent": "Mozilla/5.0 NexusGraphBot/0.1"})
        if r.status_code >= 400:
            print(f"[fetch] HTTP {r.status_code} -> using feed text: {article.url}")
            return article
        text = trafilatura.extract(r.text)
        if not text:
            print(f"[fetch] no article text found (paywall or JavaScript page) -> using feed text: {article.url}")
        elif len(text) > len(article.text):
            return article.model_copy(update={"text": text})
    except Exception as exc:
        print(f"[fetch] {type(exc).__name__} -> using feed text: {article.url}")
    return article


def relevant(article: Article) -> bool:
    kws = settings.keyword_list
    if not kws:
        return True
    hay = f"{article.title} {article.text[:3000]}".lower()
    return any(re.search(rf"\b{re.escape(k)}s?\b", hay) for k in kws)