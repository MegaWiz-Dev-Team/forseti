"""TDD Tests for SQLite Results Database — Sprint 02.

Red phase: Tests written before implementation.
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from forseti.db.results_db import ResultsDB


class TestResultsDB:
    """Test SQLite results database for Forseti."""

    def test_create_db(self):
        """DB file is created and tables exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/forseti.db")
            assert Path(f"{tmpdir}/forseti.db").exists()
            db.close()

    def test_save_test_run(self):
        """Save a test run record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/forseti.db")
            run_id = db.save_run(
                suite_name="CSH E2E",
                phase="SIT",
                base_url="http://localhost:8080",
                total=26,
                passed=24,
                failed=2,
                errors=0,
                skipped=0,
                duration_ms=5000,
            )
            assert run_id > 0
            db.close()

    def test_save_scenario_result(self):
        """Save scenario results linked to a run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/forseti.db")
            run_id = db.save_run(
                suite_name="CSH E2E", phase="SIT", base_url="http://localhost:8080",
                total=1, passed=1, failed=0, errors=0, skipped=0, duration_ms=100,
            )
            sc_id = db.save_scenario(
                run_id=run_id,
                name="TC_E2E_01",
                status="pass",
                duration_ms=50,
                error_message=None,
            )
            assert sc_id > 0
            db.close()

    def test_get_runs(self):
        """Retrieve all test runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/forseti.db")
            db.save_run("Run 1", "SIT", "http://localhost", 5, 5, 0, 0, 0, 100)
            db.save_run("Run 2", "SIT", "http://localhost", 5, 3, 2, 0, 0, 200)
            runs = db.get_runs()
            assert len(runs) == 2
            assert runs[0]["suite_name"] == "Run 2"  # newest first
            db.close()

    def test_get_run_with_scenarios(self):
        """Retrieve a run with its scenario results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/forseti.db")
            run_id = db.save_run("CSH", "SIT", "http://localhost", 2, 1, 1, 0, 0, 200)
            db.save_scenario(run_id, "TC_01", "pass", 50, None)
            db.save_scenario(run_id, "TC_02", "fail", 80, "Assertion failed")
            result = db.get_run(run_id)
            assert result["suite_name"] == "CSH"
            assert len(result["scenarios"]) == 2
            db.close()

    def test_get_trend(self):
        """Get pass rate trend across runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/forseti.db")
            db.save_run("CSH", "SIT", "http://localhost", 10, 8, 2, 0, 0, 100)
            db.save_run("CSH", "SIT", "http://localhost", 10, 9, 1, 0, 0, 100)
            db.save_run("CSH", "SIT", "http://localhost", 10, 10, 0, 0, 0, 100)
            trend = db.get_trend(limit=3)
            assert len(trend) == 3
            assert trend[0]["pass_rate"] == 100.0  # newest
            assert trend[2]["pass_rate"] == 80.0  # oldest
            db.close()
