import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from retrieval.hybrid_search import hybrid_search
from retrieval.explainer import explain
from ingestion.loader import graph, load_all


logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger()

logger.info("🔥 API FILE LOADED")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Loading data and building lineage graph...")
    load_all()
    logger.info("✅ Startup complete")
    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/search")
def search(query: str):
    logger.info("🔥 CALLING SEARCH")
    return {"results": hybrid_search(query)}


@app.get("/lineage")
def lineage(column: str):
    logger.info("🔥 CALLING LINEAGE")

    result = graph.get_multi_hop(column)

    if not result:
        return {
            "column": column,
            "status": "not_found",
            "message": f"⚠️ Column '{column}' not found"
        }

    upstream, downstream = result

    return {
        "column": column,
        "status": "found",
        "upstream": upstream,
        "downstream": downstream
    }


@app.get("/table-lineage")
def table_lineage(table: str):
    result = graph.get_table_lineage(table)

    return {"table": table, "result": result}


@app.post("/explain")
def explain_api(query: str):
    logger.info("🔥 CALLING EXPLAIN")

    res = hybrid_search(query)

    if not res:
        return {"status": "no_data"}

    docs = [r["document"] for r in res]

    explanation = explain(query, docs)

    return {"query": query, "explanation": explanation}