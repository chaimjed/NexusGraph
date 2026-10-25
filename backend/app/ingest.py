from collections.abc import Iterator

import feedparser
import httpx
import trafilatura

from .config import settings
from .schemas import Article


def fetch_entries(limit: int) -> Iterator[Article]:
    """Yield lightweight articles (no full text yet) from the configured feeds."""
    count = 0
    for feed_url in settings.feeds:
        for e in feedparser.parse(feed_url).entries:
            if count >= limit:
                return
            yield Article(
                url=e.get("link", ""),
                title=e.get("title", ""),
                published=e.get("published", ""),
                text=e.get("summary", ""),
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
