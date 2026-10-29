from . import extract, graph_store, ingest, resolve
from .schemas import Article


def process(article: Article, store: bool = True):
    """extract -> resolve names against the graph -> (optionally) store."""
    known = graph_store.known_entities()
    raw = extract.extract(article, known)
    result, alias_updates = resolve.resolve(raw, known)
    n = 0
    if store:
        n = graph_store.upsert_extraction(article.url, result)
        graph_store.add_aliases(alias_updates)
    return result, n


def run(limit: int = 10, force: bool = False) -> dict:
    stats = {"seen_in_feeds": 0, "skipped_known": 0, "skipped_irrelevant": 0,
             "processed": 0, "relations": 0, "errors": 0}
    items = []
    for entry in ingest.fetch_entries(limit):
        stats["seen_in_feeds"] += 1
        item = {"title": entry.title[:90], "status": ""}
        items.append(item)
        if not entry.url:
            item["status"] = "skipped: no url"
            continue
        if not force and graph_store.article_seen(entry.url):
            stats["skipped_known"] += 1
            item["status"] = "skipped: already processed (use force=true to redo)"
            continue
        try:
            article = ingest.load_text(entry)
            if not ingest.relevant(article):
                stats["skipped_irrelevant"] += 1
                item["status"] = "skipped: no keyword match"
                continue
            _, n = process(article)
            graph_store.mark_article(article)
            stats["relations"] += n
            stats["processed"] += 1
            item.update(status="ok", relations=n, chars=len(article.text))
        except Exception as exc:
            stats["errors"] += 1
            item.update(status="error", error=f"{type(exc).__name__}: {str(exc)[:300]}")
    return {"stats": stats, "items": items}