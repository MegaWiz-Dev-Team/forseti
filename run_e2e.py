"""Run Forseti E2E against the live dev server.

Supports environment variables:
  E2E_BASE_URL       — target URL (default: http://localhost:8080)
  TEST_ADMIN_EMAIL   — admin email
  TEST_ADMIN_PASSWORD — admin password
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load .env from cloud-super-hero project (local dev only)
try:
    from dotenv import load_dotenv
    csh_env = Path(__file__).parent.parent / "cloud-super-hero" / ".env"
    if csh_env.exists():
        load_dotenv(csh_env)
except ImportError:
    pass  # dotenv not required in CI

from forseti.agents.orchestrator import ForsetiOrchestrator
from forseti.db.results_db import ResultsDB

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def main():
    db = ResultsDB(db_path="forseti_results.db")

    base_url = os.getenv("E2E_BASE_URL", "http://localhost:8080")

    orch = ForsetiOrchestrator(
        base_url=base_url,
        admin_email=os.getenv("TEST_ADMIN_EMAIL", "paripol@megawiz.co"),
        admin_password=os.getenv("TEST_ADMIN_PASSWORD", "MyHero@2026"),
        db=db,
        report_dir="reports",
    )

    yaml_path = str(Path(__file__).parent / "examples" / "test_scripts" / "cloud_super_hero_e2e.yaml")

    report = await orch.run_all(yaml_path)

    print("\n" + "=" * 60)
    print(report["summary"])
    print(f"   ISO Report: {report['iso_report_path']}")
    print(f"   SQLite Run ID: {report['run_id']}")
    if report["github_issue"]:
        title, body = report["github_issue"]
        print(f"   GitHub Issue: {title}")
    else:
        print("   GitHub Issue: None (all passed! 🎉)")
    print("=" * 60)

    db.close()

    # Exit with code 1 if any tests failed (for CI/CD)
    if report.get("failed", 0) > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

