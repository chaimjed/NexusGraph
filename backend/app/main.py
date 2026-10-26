from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from . import graph_store, pipeline
from .schemas import Article


@asynccontextmanager
async def lifespan(app: FastAPI):
    graph_store.init_schema()
    yield
    graph_store.close()


app = FastAPI(title="NexusGraph AI", version="0.1.0", lifespan=lifespan)


class DebugIn(BaseModel):
    text: str
    store: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/debug/extract")
def debug_extract(body: DebugIn):
    """Test the full extract + resolve path on any text. store=true writes to Neo4j."""
    art = Article(url="debug://manual", title="manual test", text=body.text)
    try:
        result, _ = pipeline.process(art, store=body.store)
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}")


@app.post("/ingest")
def ingest_news(limit: int = Query(10, ge=1, le=50), force: bool = False):
    return pipeline.run(limit, force)


@app.get("/graph")
def graph(limit: int = Query(200, ge=1, le=2000)):
    return graph_store.export_graph(limit)


@app.get("/impact")
def impact(q: str, max_hops: int = Query(4, ge=1, le=6)):
    return graph_store.impact_paths(q, max_hops)


@app.get("/risks/critical-suppliers")
def critical(min_customers: int = Query(2, ge=1)):
    return graph_store.critical_suppliers(min_customers)