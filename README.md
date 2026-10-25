# NexusGraph AI — Autonomous Market Intelligence Engine

Turns noisy supply-chain news into a **Neo4j knowledge graph** and answers multi-hop
questions such as *"How does the neon-gas export ban hit Intel?"* by traversing
`Event → Material → Company` paths instead of matching text chunks.

## Status — Phase 1 (this commit)
- [x] RSS ingestion + full-text fetch (trafilatura)
- [x] LLM structured extraction (hosted LLM, Pydantic schema, confidence filter)
- [x] Neo4j upsert with provenance (source URLs, evidence quote, confidence)
- [x] REST API: `/ingest`, `/graph`, `/impact`, `/risks/critical-suppliers`
- [x] Docker Compose (Neo4j + API)

## Roadmap
2. Hand-labelled eval set (≈50 articles): extraction precision/recall; vector-RAG vs GraphRAG on 20 multi-hop questions
3. Hybrid retrieval (Neo4j vector index + graph traversal) and `/ask` endpoint with cited paths
4. LangGraph workflow: extract → reconcile (contradiction/update) → risk-score → alert webhook
5. Graph UI (Next.js + force-graph), Playwright E2E test, Logfire tracing
6. One dynamic-site scraper (Selenium/Playwright) for pages RSS can't cover

## Quickstart
```bash
cp .env.example .env        # add ANTHROPIC_API_KEY
docker compose up --build
curl -X POST "localhost:8000/ingest?limit=10"
curl "localhost:8000/impact?q=export"
curl "localhost:8000/risks/critical-suppliers"
```
Neo4j Browser: http://localhost:7474 (neo4j / nexusgraph) — try `MATCH p=()-[]->() RETURN p LIMIT 50`.

## Graph model
Edge direction = direction a disruption propagates:
`Event -AFFECTS-> *`, `Location -HOSTS-> Company`, `Company -SUPPLIES-> Company`, `Material|Product -INPUT_TO-> Product|Company`.
This makes impact analysis a plain directed path query.

## Tests
```bash
cd backend && pip install -r requirements.txt && pytest
```
