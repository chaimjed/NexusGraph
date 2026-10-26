from . import llm
from .config import settings
from .schemas import Article, Extraction

SYSTEM = """You extract supply-chain knowledge-graph relations from news articles.
Only extract relations explicitly supported by the article text; never guess.
Naming rules:
- Use the shortest common name, and acronyms when they are standard (TSMC, not "Taiwan Semiconductor Manufacturing Company"; Intel, not "Intel Corp.").
- Resolve phrases like "the chipmaker" or "the foundry" to the company they refer to; never create entities for them.
- If an entity is listed under "already in the graph", reuse that exact name.
- Skip vague statements with no concrete entities (e.g. "companies are diversifying").
Edge direction = direction a disruption propagates:
- AFFECTS: Event -> Location/Company/Material/Product
- HOSTS: Location -> Company (company has facilities/operations there)
- SUPPLIES: supplier Company -> customer Company
- INPUT_TO: Material/Product -> Product/Company that consumes it
Give each relation a short verbatim evidence quote and a confidence in [0,1].
If the article has no relevant relations, return an empty list."""


def known_block(known: list[dict] | None) -> str:
    if not known:
        return ""
    groups: dict[str, list[str]] = {}
    for k in known[:300]:
        if k["type"] != "Event":
            groups.setdefault(k["type"], []).append(k["name"])
    if not groups:
        return ""
    lines = "\n".join(f"{t}: {', '.join(names)}" for t, names in groups.items())
    return f"Entities already in the graph:\n{lines}\n\n"


def clean(result: Extraction, min_confidence: float | None = None) -> Extraction:
    threshold = settings.min_confidence if min_confidence is None else min_confidence
    seen, kept = set(), []
    for r in result.relations:
        src, tgt = " ".join(r.source.split()), " ".join(r.target.split())
        if not src or not tgt or src.casefold() == tgt.casefold():
            continue
        if r.confidence < threshold:
            continue
        key = (src.casefold(), r.source_type, r.relation, tgt.casefold(), r.target_type)
        if key in seen:
            continue
        seen.add(key)
        kept.append(r.model_copy(update={"source": src, "target": tgt}))
    return Extraction(relations=kept)


def extract(article: Article, known: list[dict] | None = None) -> Extraction:
    body = (
        f"{known_block(known)}Title: {article.title}\nPublished: {article.published}\n\n"
        f"{article.text[: settings.max_chars]}"
    )
    return clean(llm.extract_structured(Extraction, SYSTEM, body))