from contextlib import asynccontextmanager

from fastapi import FastAPI, Query

from . import graph_store, pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    graph_store.init_schema()
    yield
    graph_store.close()


app = FastAPI(title="NexusGraph AI", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest_news(limit: int = Query(10, ge=1, le=50)):
    return pipeline.run(limit)


@app.get("/graph")
def graph(limit: int = Query(200, ge=1, le=2000)):
    return graph_store.export_graph(limit)


@app.get("/impact")
def impact(q: str, max_hops: int = Query(4, ge=1, le=6)):
    return graph_store.impact_paths(q, max_hops)


@app.get("/risks/critical-suppliers")
def critical(min_customers: int = Query(2, ge=1)):
    return graph_store.critical_suppliers(min_customers)
