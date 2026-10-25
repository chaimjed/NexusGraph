import re
from collections.abc import Iterator

import feedparser
import httpx
import trafilatura

from .config import settings
from .schemas import Article

TAG = re.compile(r"<[^>]+>")


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
                    text=TAG.sub(" ", e.get("summary", "")).strip(),
                )
                count += 1


def load_text(article: Article) -> Article:
    """Try to fetch the full article text; fall back to the RSS summary."""
    try:
        r = httpx.get(article.url, follow_redirects=True, timeout=15,
                      headers={"User-Agent": "Mozilla/5.0 NexusGraphBot/0.1"})
        text = trafilatura.extract(r.text)
        if text and len(text) > len(article.text):
            return article.model_copy(update={"text": text})
    except Exception:
        pass
    return article


def relevant(article: Article) -> bool:
    kws = settings.keyword_list
    if not kws:
        return True
    hay = f"{article.title} {article.text[:3000]}".lower()
    return any(re.search(rf"\b{re.escape(k)}s?\b", hay) for k in kws)