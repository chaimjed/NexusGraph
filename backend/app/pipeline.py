from . import extract, graph_store, ingest


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
            result = extract.extract(article)
            n = graph_store.upsert_extraction(article.url, result)
            graph_store.mark_article(article)
            stats["relations"] += n
            stats["processed"] += 1
            item.update(status="ok", relations=n)
        except Exception as exc:
            stats["errors"] += 1
            item.update(status="error", error=f"{type(exc).__name__}: {str(exc)[:300]}")
    return {"stats": stats, "items": items}