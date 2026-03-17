"""SQLite Results Database for Forseti — Sprint 02.

Persistent storage for test run results with trend tracking.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class ResultsDB:
    """SQLite database for persisting test results.

    Schema:
        runs       — one row per test execution (suite run)
        scenarios  — one row per scenario result, linked to a run
    """

    def __init__(self, db_path: str = "forseti_results.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                suite_name  TEXT NOT NULL,
                phase       TEXT NOT NULL,
                base_url    TEXT NOT NULL,
                total       INTEGER NOT NULL,
                passed      INTEGER NOT NULL,
                failed      INTEGER NOT NULL,
                errors      INTEGER NOT NULL DEFAULT 0,
                skipped     INTEGER NOT NULL DEFAULT 0,
                pass_rate   REAL NOT NULL,
                duration_ms INTEGER NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scenarios (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id       INTEGER NOT NULL,
                name         TEXT NOT NULL,
                status       TEXT NOT NULL,
                duration_ms  INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at   TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );
        """)
        self.conn.commit()

    def save_run(
        self,
        suite_name: str,
        phase: str,
        base_url: str,
        total: int,
        passed: int,
        failed: int,
        errors: int,
        skipped: int,
        duration_ms: int,
    ) -> int:
        """Insert a test run record.

        Returns:
            Auto-generated run ID.
        """
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        now = datetime.now().isoformat()

        cursor = self.conn.execute(
            """INSERT INTO runs (suite_name, phase, base_url, total, passed,
               failed, errors, skipped, pass_rate, duration_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (suite_name, phase, base_url, total, passed, failed,
             errors, skipped, round(pass_rate, 1), duration_ms, now),
        )
        self.conn.commit()
        return cursor.lastrowid

    def save_scenario(
        self,
        run_id: int,
        name: str,
        status: str,
        duration_ms: int,
        error_message: str | None,
    ) -> int:
        """Insert a scenario result linked to a run.

        Returns:
            Auto-generated scenario ID.
        """
        now = datetime.now().isoformat()
        cursor = self.conn.execute(
            """INSERT INTO scenarios (run_id, name, status, duration_ms,
               error_message, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, name, status, duration_ms, error_message, now),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_runs(self, limit: int = 20) -> list[dict]:
        """Get all test runs, newest first."""
        rows = self.conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_run(self, run_id: int) -> dict | None:
        """Get a single run with its scenario results."""
        row = self.conn.execute(
            "SELECT * FROM runs WHERE id = ?", (run_id,)
        ).fetchone()

        if not row:
            return None

        run = dict(row)
        scenarios = self.conn.execute(
            "SELECT * FROM scenarios WHERE run_id = ? ORDER BY id",
            (run_id,),
        ).fetchall()
        run["scenarios"] = [dict(s) for s in scenarios]
        return run

    def get_trend(self, limit: int = 10) -> list[dict]:
        """Get pass rate trend (newest first)."""
        rows = self.conn.execute(
            """SELECT id, suite_name, pass_rate, total, passed, failed,
               duration_ms, created_at
               FROM runs ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
