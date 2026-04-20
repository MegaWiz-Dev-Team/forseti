"""⚖️ Forseti — Multi-Project E2E Runner.

Usage:
  python run_e2e.py --project cloud-super-hero   # single project
  python run_e2e.py --project forseti-self        # self-test
  python run_e2e.py --all                         # all projects
  python run_e2e.py                               # legacy CSH mode
"""
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load .env (local dev only)
try:
    from dotenv import load_dotenv
    csh_env = Path(__file__).parent.parent / "cloud-super-hero" / ".env"
    if csh_env.exists():
        load_dotenv(csh_env)
except ImportError:
    pass  # dotenv not required in CI

from forseti.agents.orchestrator import ForsetiOrchestrator
from forseti.config import load_projects
from forseti.db.results_db import ResultsDB

logging.basicConfig(level=logging.INFO, format="%(message)s")
ROOT = Path(__file__).parent


async def run_project(name: str, config, db: ResultsDB) -> dict:
    """Run E2E for a single project config."""
    print(f"\n{'='*60}")
    print(f"⚖️  Project: {name}")
    print(f"   URL: {config.base_url}")
    print(f"{'='*60}")

    orch = ForsetiOrchestrator.from_project(
        project=config, db=db, report_dir="reports",
    )

    yaml_path = str(ROOT / config.test_script)
    report = await orch.run_all(yaml_path)

    if "skipped" in report and report["skipped"]:
        print(f"\n⏭️ SKIPPED — {report.get('reason', 'Unknown reason')}")
        return report

    print(f"\n{report['summary']}")
    print(f"   ISO Report: {report.get('iso_report_path', 'N/A')}")
    print(f"   SQLite Run ID: {report.get('run_id', 'N/A')}")
    if report.get("github_issue"):
        title, _ = report["github_issue"]
        print(f"   GitHub Issue: {title}")
    else:
        print("   GitHub Issue: None (all passed! 🎉)")

    return report


async def main():
    parser = argparse.ArgumentParser(description="⚖️ Forseti E2E Runner")
    parser.add_argument("--project", "-p", help="Run specific project from forseti.yaml")
    parser.add_argument("--all", "-a", action="store_true", help="Run all projects")
    parser.add_argument("--config", "-c", default="forseti.yaml", help="Config file path")
    args = parser.parse_args()

    db = ResultsDB(db_path="forseti_results.db")
    total_failed = 0

    if args.project or args.all:
        # Multi-project mode
        config_path = str(ROOT / args.config)
        projects = load_projects(config_path)

        if args.project:
            if args.project not in projects:
                print(f"❌ Project '{args.project}' not found in {args.config}")
                print(f"   Available: {', '.join(projects.keys())}")
                sys.exit(1)
            targets = {args.project: projects[args.project]}
        else:
            targets = projects

        for name, config in targets.items():
            report = await run_project(name, config, db)
            total_failed += report.get("failed", 0)
    else:
        # Legacy single-project mode (backwards compatible)
        base_url = os.getenv("E2E_BASE_URL", "http://localhost:8080")
        orch = ForsetiOrchestrator(
            base_url=base_url,
            admin_email=os.getenv("TEST_ADMIN_EMAIL", "paripol@megawiz.co"),
            admin_password=os.getenv("TEST_ADMIN_PASSWORD", "MyHero@2026"),
            db=db,
            report_dir="reports",
        )
        yaml_path = str(ROOT / "examples" / "test_scripts" / "cloud_super_hero_e2e.yaml")
        report = await orch.run_all(yaml_path)

        print("\n" + "=" * 60)
        print(report["summary"])
        print(f"   ISO Report: {report['iso_report_path']}")
        print(f"   SQLite Run ID: {report['run_id']}")
        if report["github_issue"]:
            title, _ = report["github_issue"]
            print(f"   GitHub Issue: {title}")
        else:
            print("   GitHub Issue: None (all passed! 🎉)")
        print("=" * 60)
        total_failed = report.get("failed", 0)

    db.close()

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
