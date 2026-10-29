from neo4j import GraphDatabase

from .config import settings
from .schemas import Article, Extraction, entity_key

_driver = None


def driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver


def close():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def run(query: str, **params) -> list[dict]:
    with driver().session() as s:
        return [r.data() for r in s.run(query, **params)]


def init_schema():
    run("CREATE CONSTRAINT entity_key IF NOT EXISTS FOR (e:Entity) REQUIRE e.key IS UNIQUE")
    run("CREATE CONSTRAINT article_url IF NOT EXISTS FOR (a:Article) REQUIRE a.url IS UNIQUE")


def article_seen(url: str) -> bool:
    return bool(run("MATCH (a:Article {url:$url}) RETURN a.url AS u", url=url))


def mark_article(a: Article):
    run("MERGE (a:Article {url:$url}) SET a.title=$title, a.published=$pub, a.processed_at=datetime()",
        url=a.url, title=a.title, pub=a.published)


def upsert_extraction(url: str, result: Extraction) -> int:
    for r in result.relations:
        # r.relation is a validated enum, so interpolating it into Cypher is safe
        run(
            f"""
            MERGE (s:Entity {{key:$skey}}) ON CREATE SET s.name=$sname, s.type=$stype, s.aliases=[]
            MERGE (t:Entity {{key:$tkey}}) ON CREATE SET t.name=$tname, t.type=$ttype, t.aliases=[]
            MERGE (s)-[rel:{r.relation.value}]->(t)
            ON CREATE SET rel.first_seen=datetime()
            SET rel.last_seen=datetime(),
                rel.confidence=CASE WHEN rel.confidence IS NULL OR $conf > rel.confidence THEN $conf ELSE rel.confidence END,
                rel.sources=CASE WHEN $url IN coalesce(rel.sources, []) THEN rel.sources
                                 ELSE coalesce(rel.sources, []) + $url END,
                rel.evidence=$evidence
            """,
            skey=entity_key(r.source, r.source_type), sname=r.source, stype=r.source_type.value,
            tkey=entity_key(r.target, r.target_type), tname=r.target, ttype=r.target_type.value,
            conf=r.confidence, url=url, evidence=r.evidence,
        )
    return len(result.relations)


def export_graph(limit: int = 200) -> dict:
    nodes = run("MATCH (n:Entity) RETURN n.key AS id, n.name AS name, n.type AS type LIMIT $limit", limit=limit)
    edges = run(
        """MATCH (a:Entity)-[r]->(b:Entity)
           RETURN a.key AS source, b.key AS target, type(r) AS relation,
                  r.confidence AS confidence, r.sources AS sources, r.evidence AS evidence
           LIMIT $limit""",
        limit=limit,
    )
    return {"nodes": nodes, "edges": edges}


def impact_paths(query: str, max_hops: int = 4) -> list[dict]:
    hops = max(1, min(int(max_hops), 6))
    return run(
        f"""
        MATCH p=(ev:Entity {{type:'Event'}})-[:AFFECTS|HOSTS|SUPPLIES|INPUT_TO*1..{hops}]->(c:Entity {{type:'Company'}})
        WHERE toLower(ev.name) CONTAINS toLower($q)
        RETURN [n IN nodes(p) | n.name] AS path,
               [r IN relationships(p) | type(r)] AS relations,
               length(p) AS hops
        ORDER BY hops LIMIT 25
        """,
        q=query,
    )


def critical_suppliers(min_customers: int = 2) -> list[dict]:
    return run(
        """
        MATCH (s:Entity)-[:SUPPLIES]->(c:Entity {type:'Company'})
        WITH s, collect(DISTINCT c.name) AS customers
        WHERE size(customers) >= $n
        RETURN s.name AS supplier, customers, size(customers) AS exposure
        ORDER BY exposure DESC
        """,
        n=min_customers,
    )
def known_entities(limit: int = 300) -> list[dict]:
    return run(
        "MATCH (e:Entity) RETURN e.name AS name, e.type AS type, "
        "coalesce(e.aliases, []) AS aliases ORDER BY e.name LIMIT $limit",
        limit=limit,
    )


def add_aliases(updates: list[tuple]):
    for etype, name, alias in updates:
        run(
            """MATCH (e:Entity {key:$key})
               SET e.aliases = coalesce(e.aliases, []) +
                   [a IN [$alias] WHERE NOT a IN coalesce(e.aliases, [])]""",
            key=entity_key(name, etype), alias=alias,
        )
_PATH_RETURN = """
RETURN [n IN nodes(p) | {name: n.name, type: n.type}] AS nodes,
       [r IN relationships(p) | {type: type(r), evidence: r.evidence,
                                 sources: r.sources, confidence: r.confidence}] AS edges
LIMIT $limit
"""


def paths_from(key: str, max_hops: int = 3, limit: int = 80) -> list[dict]:
    """Everything a disruption at this entity can reach (follows edge direction)."""
    h = max(1, min(int(max_hops), 4))
    return run(f"MATCH p=(s:Entity {{key:$key}})-[*1..{h}]->(t:Entity) {_PATH_RETURN}", key=key, limit=limit)


def paths_to(key: str, max_hops: int = 3, limit: int = 80) -> list[dict]:
    """Everything that can propagate a disruption into this entity (its upstream dependencies)."""
    h = max(1, min(int(max_hops), 4))
    return run(f"MATCH p=(t:Entity)-[*1..{h}]->(s:Entity {{key:$key}}) {_PATH_RETURN}", key=key, limit=limit)