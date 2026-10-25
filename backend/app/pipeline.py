from . import extract, graph_store, ingest


def run(limit: int = 10) -> dict:
    stats = {"seen_in_feeds": 0, "skipped_known": 0, "processed": 0, "relations": 0, "errors": 0}
    for entry in ingest.fetch_entries(limit):
        stats["seen_in_feeds"] += 1
        if not entry.url or graph_store.article_seen(entry.url):
            stats["skipped_known"] += 1
            continue
        try:
            article = ingest.load_text(entry)
            result = extract.extract(article)
            stats["relations"] += graph_store.upsert_extraction(article.url, result)
            graph_store.mark_article(article)
            stats["processed"] += 1
        except Exception as exc:  # keep the batch going; Logfire tracing comes later
            stats["errors"] += 1
            print(f"[pipeline] failed on {entry.url}: {exc}")
    return stats
