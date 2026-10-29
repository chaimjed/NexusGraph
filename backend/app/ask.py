"""Question answering over the knowledge graph (step 1: graph paths, no LLM)."""
import re

from . import graph_store, resolve
from .schemas import entity_key

UPSTREAM = re.compile(
    r"\b(suppliers?|supplied by|depends? on|dependenc\w*|rel(?:y|ies) on)\b"
    r"|\b(who|which companies|what companies)\b.*\b(supplies|supply|sells)\b",
    re.I,
)


def detect_direction(question: str) -> str:
    """'upstream' = who feeds this entity; 'downstream' = what a disruption here reaches."""
    return "upstream" if UPSTREAM.search(question) else "downstream"


def link_entities(question: str, known: list[dict]) -> list[dict]:
    """Find graph entities mentioned in the question (names, learned aliases, well-known companies)."""
    q = f" {resolve.norm(question)} "
    by_name = {k["name"].casefold(): k for k in known}
    found: dict[str, dict] = {}
    for k in known:
        forms = {resolve.norm(k["name"]), *(k.get("aliases") or [])}
        if any(len(f) >= 3 and f" {f} " in q for f in forms):
            found[entity_key(k["name"], k["type"])] = k
    for form, canon in resolve.SEED_INDEX.items():
        if len(form) >= 3 and f" {form} " in q and canon.casefold() in by_name:
            k = by_name[canon.casefold()]
            found[entity_key(k["name"], k["type"])] = k
    return list(found.values())


def format_path(row: dict) -> dict:
    names = [n["name"] for n in row["nodes"]]
    chain = names[0] + "".join(f" -{e['type']}-> {n}" for e, n in zip(row["edges"], names[1:]))
    confs = [e["confidence"] for e in row["edges"] if e.get("confidence") is not None]
    sources = sorted({s for e in row["edges"] for s in (e.get("sources") or [])})
    return {
        "chain": chain,
        "hops": len(row["edges"]),
        "weakest_confidence": min(confs) if confs else None,
        "evidence": [e.get("evidence") for e in row["edges"]],
        "sources": sources,
    }


def answer(question: str, max_hops: int = 3, max_paths: int = 20) -> dict:
    known = graph_store.known_entities(1000)
    entities = link_entities(question, known)
    direction = detect_direction(question)
    base = {"question": question, "direction": direction, "entities": [e["name"] for e in entities]}
    if not entities:
        return {**base, "paths": [], "related_companies": [],
                "note": "No entity from the graph was found in the question.",
                "known_entities": sorted(k["name"] for k in known)[:40]}

    mentioned = {e["name"].casefold() for e in entities}
    rows = []
    for e in entities:
        key = entity_key(e["name"], e["type"])
        rows += (graph_store.paths_from(key, max_hops) if direction == "downstream"
                else graph_store.paths_to(key, max_hops))
    if len(entities) >= 2:  # keep only paths that connect the entities you asked about
        rows = [r for r in rows if sum(n["name"].casefold() in mentioned for n in r["nodes"]) >= 2]

    paths, seen = [], set()
    for r in sorted(rows, key=lambda r: len(r["edges"])):
        p = format_path(r)
        if p["chain"] not in seen:
            seen.add(p["chain"])
            paths.append((p, r))
    paths = paths[:max_paths]

    end = -1 if direction == "downstream" else 0       # the far end of each path
    start = 0 if direction == "downstream" else -1     # the entity the question is about
    related = sorted({r["nodes"][end]["name"] for _, r in paths if r["nodes"][end]["type"] == "Company"})
    focus = sorted({r["nodes"][start]["name"] for _, r in paths})
    if not related:
        summary = "The graph has no connecting paths for this question yet."
    elif direction == "downstream":
        summary = f"A disruption at {', '.join(focus)} can reach: {', '.join(related)}."
    else:
        summary = f"{', '.join(focus)} depends on: {', '.join(related)}."
    return {**base, "summary": summary, "related_companies": related, "paths": [p for p, _ in paths]}