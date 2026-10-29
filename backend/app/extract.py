import re

from . import llm
from .config import settings
from .schemas import Article, EntityType as E, Extraction, RelationType as R

SYSTEM = """You extract supply-chain knowledge-graph relations from news articles.
Only extract relations explicitly supported by the article text; never guess.

Naming rules:
- Use the shortest common name, and acronyms when they are standard (TSMC, not "Taiwan Semiconductor Manufacturing Company"; Intel, not "Intel Corp.").
- Resolve phrases like "the chipmaker" or "the foundry" to the company they refer to; never create entities for them.
- If an entity is listed under "already in the graph", reuse that exact name.
- Skip vague statements with no concrete entities (e.g. "companies are diversifying").

Relation types (edge direction = direction a disruption propagates):
- SUPPLIES: supplier Company -> customer Company. Use ONLY when the text says one company sells, ships, manufactures for, or provides products, services or materials to another company. Never use it for: competitors or "alternatives" to a company, partners, "works with" or "backed by" statements, supporters or members of an alliance, investors, or shipments to a country (countries are not customers). A government approval or licence to buy is an Event, not a supply relation.
  Examples of text that does NOT contain a supply relation (invented companies):
  "Regulators cleared Alpha Corp and Beta Ltd to buy Gamma's processors, but nothing has been delivered" -> no SUPPLIES (a clearance is an Event that AFFECTS the companies).
  "Delta is regarded as a rival to Gamma" -> nothing. "Epsilon collaborates with Gamma on research" -> nothing.
- INPUT_TO: Material/Product -> Product/Company that consumes it.
- HOSTS: Location -> Company. Use ONLY when the text says the company has a factory, fab, plant, office, expansion or operations in that place. Ignore press-release datelines, mailing addresses and boilerplate such as "Paris, France--(Newsfile Corp.) - Company X announced".
- AFFECTS: Event -> Location/Company/Material/Product.
- Government actions (export controls, sanctions, tariffs, investigations, bans) are Events: give them a descriptive name with the year, and link them with AFFECTS to the companies, locations or products they concern.

Give each relation a short verbatim evidence quote and a confidence in [0,1]: use 0.9+ only when the text states it directly; use 0.7 or less when you are inferring.
If the article has no relevant relations, return an empty list."""

# "Paris, France--(Newsfile Corp. ..." style press-release datelines are not facts about operations
DATELINE = re.compile(r"[A-Za-z.\s]+,\s*[A-Za-z.\s]+--\s*\(")

# Guardrail: an approval/licence "to buy" is not a supply relation unless the text also describes a delivery
APPROVAL = re.compile(r"\b(approv\w*|licen[sc]\w*|permit\w*|authori[sz]\w*|clear(?:ed|ing|ance))\b", re.I)
DELIVERY = re.compile(r"\b(suppl\w*|ship\w*|deliver\w*|sold|sell\w*|manufactur\w*)\b", re.I)

# Which entity types each relation may connect: (source types, target types)
ALLOWED = {
    R.SUPPLIES: ({E.COMPANY}, {E.COMPANY}),
    R.HOSTS: ({E.LOCATION}, {E.COMPANY}),
    R.INPUT_TO: ({E.MATERIAL, E.PRODUCT}, {E.PRODUCT, E.COMPANY}),
    R.AFFECTS: ({E.EVENT}, {E.LOCATION, E.COMPANY, E.MATERIAL, E.PRODUCT}),
}


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


def valid_types(r) -> bool:
    src_ok, tgt_ok = ALLOWED[r.relation]
    return r.source_type in src_ok and r.target_type in tgt_ok


def clean(result: Extraction, min_confidence: float | None = None) -> Extraction:
    threshold = settings.min_confidence if min_confidence is None else min_confidence
    seen, kept = set(), []
    for r in result.relations:
        src, tgt = " ".join(r.source.split()), " ".join(r.target.split())
        if not src or not tgt or src.casefold() == tgt.casefold():
            continue
        if r.confidence < threshold or not valid_types(r):
            continue
        if r.relation == R.HOSTS and DATELINE.search(r.evidence):
            continue
        if r.relation == R.SUPPLIES and APPROVAL.search(r.evidence) and not DELIVERY.search(r.evidence):
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