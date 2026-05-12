"""Forseti MCP Server — exposes E2E testing automation tools."""

import asyncio
from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP(
    name="forseti",
    dependencies=["forseti"]
)

@mcp_server.tool()
async def list_available_test_projects() -> list[str]:
    """List all available project configurations that can be tested via Forseti."""
    from forseti.config import load_projects
    from pathlib import Path
    import os
    
    # Locate forseti.yaml in the root project directory (current working directory)
    config_path = str(Path(os.getcwd()) / "forseti.yaml")
    try:
        projects = load_projects(config_path)
        return list(projects.keys())
    except Exception as e:
        return [f"Error loading projects: {e}"]

@mcp_server.tool()
async def run_e2e_tests(project_name: str) -> str:
    """Trigger an End-to-End automated test suite for a specific project.
    
    This runs real headless browsers and LLM orchestration in the background.
    Returns the console output and testing summary.
    """
    import subprocess
    cmd = f"python run_e2e.py --project {project_name}"
    
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    output = stdout.decode()
    if stderr:
        output += "\n--- STDERR ---\n" + stderr.decode()
        
    return output

@mcp_server.tool()
async def get_recent_test_runs(limit: int = 5) -> str:
    """Get the recent test run results from the Forseti dashboard SQLite database."""
    from forseti.db.results_db import ResultsDB
    import os

    db_path = os.environ.get("DB_PATH", "forseti_results.db")
    db = ResultsDB(db_path=db_path)
    runs = db.get_runs(limit=limit)
    db.close()
    
    if not runs:
        return "No recent runs found."
        
    # Format nicely
    summary = []
    for r in runs:
        summary.append(f"Run #{r['id']} | Suite: {r['suite_name']} | Passed: {r['passed']}/{r['total']} | Status: {r['status']}")
    
    return "\n".join(summary)
