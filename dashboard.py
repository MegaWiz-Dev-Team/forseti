"""⚖️ Forseti Web Report Dashboard — serve test results from SQLite + MCP SSE endpoint."""
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).parent / "src"))
from forseti.db.results_db import ResultsDB

# Initialize FastAPI App
app = FastAPI(title="Forseti Dashboard and MCP Server")

DB_PATH = os.environ.get("DB_PATH", "/app/data/forseti_results.db")

# ── 1. Mount MCP FastMCP Application ──
from forseti.api.mcp import mcp_server
app.mount("/mcp", mcp_server.sse_app())

def get_db():
    """Create a fresh DB connection per request (thread-safe)."""
    return ResultsDB(db_path=DB_PATH)

# ── 2. Dashboard Web Interface ──
@app.get("/")
async def index():
    return FileResponse("web/dashboard/index.html")

@app.get("/api/suites")
async def api_suites():
    db = get_db()
    suites = db.get_suites()
    db.close()
    return suites

@app.get("/api/runs")
async def api_runs(suite: str | None = None):
    db = get_db()
    runs = db.get_runs(limit=50, suite=suite)
    db.close()
    return runs

@app.get("/api/runs/{run_id}")
async def api_run_detail(run_id: int):
    db = get_db()
    run = db.get_run(run_id)
    db.close()
    if not run:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return run

@app.get("/api/trend")
async def api_trend(suite: str | None = None):
    db = get_db()
    trend = db.get_trend(limit=20, suite=suite)
    db.close()
    return trend

@app.get("/api/runs/{run_id}/feedback")
async def api_run_feedback(run_id: int):
    db = get_db()
    feedback = db.get_feedback(run_id)
    db.close()
    return feedback

@app.post("/api/runs", status_code=201)
async def api_submit_run(request: Request):
    """Accept external test results (unit/e2e/ui) from any Asgard service."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON mapping"})
        
    if not data or "suite_name" not in data:
        return JSONResponse(status_code=400, content={"error": "suite_name required"})

    db = get_db()
    run_id = db.save_run(
        suite_name=data["suite_name"],
        phase=data.get("phase", "SIT"),
        base_url=data.get("base_url", ""),
        total=data.get("total", 0),
        passed=data.get("passed", 0),
        failed=data.get("failed", 0),
        errors=data.get("errors", 0),
        skipped=data.get("skipped", 0),
        duration_ms=data.get("duration_ms", 0),
        project_version=data.get("project_version", "unknown"),
        project_commit=data.get("project_commit", "unknown"),
    )

    # Save individual scenarios if provided
    for sc in data.get("scenarios", []):
        db.save_scenario(
            run_id=run_id,
            name=sc.get("name", "unknown"),
            status=sc.get("status", "unknown"),
            duration_ms=sc.get("duration_ms", 0),
            error_message=sc.get("error_message"),
        )

    db.close()
    return {"id": run_id, "status": "saved"}

# Mount fallback static files (if index.html references internal assets like CSS/JS files natively)
app.mount("/", StaticFiles(directory="web/dashboard"), name="static")

if __name__ == "__main__":
    import uvicorn
    print("⚖️ Forseti Dashboard — http://localhost:5555")
    print("🤖 Forseti MCP Server — http://localhost:5555/mcp/sse")
    uvicorn.run("dashboard:app", host="0.0.0.0", port=5555, reload=True)
