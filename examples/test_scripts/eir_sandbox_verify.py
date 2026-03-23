#!/usr/bin/env python3
"""⚖️ Forseti — Eir Sandbox Database Verification Runner.

Standalone script to verify Eir sandbox database migrations and mock data.
Connects to MariaDB via Docker exec and validates row counts + data integrity.

Usage:
    python eir_sandbox_verify.py
    python eir_sandbox_verify.py --host localhost --port 3306
    python eir_sandbox_verify.py --docker asgard_mariadb
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class SandboxVerifier:
    """Verifies Eir sandbox database integrity."""

    EXPECTED_COUNTS = {
        "patient_data": 5,
        "form_encounter": 5,
        "forms": 7,
        "lbf_data": 100,
        "layout_group_properties": 8,
        "layout_options": 28,
        "list_options": 25,
        "registry": 2,
        "migration_log": 10,
    }

    TRIAGE_CHECKS = {
        5011: ("green", "2.3"),    # Patient 1001 - Day 1
        5012: ("green", "1.9"),    # Patient 1001 - Day 2
        5013: ("yellow", "8.7"),   # Patient 1002
        5014: ("red", "28.4"),     # Patient 1003
    }

    def __init__(self, docker_container: str = "asgard_mariadb",
                 db_user: str = "openemr", db_pass: str = "openemr",
                 db_name: str = "openemr_sandbox"):
        self.container = docker_container
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.results = []

    def _run_sql(self, query: str) -> str:
        """Execute SQL via docker exec and return output."""
        cmd = [
            "docker", "exec", self.container,
            "mariadb", f"-u{self.db_user}", f"-p{self.db_pass}",
            self.db_name, "-N", "-B", "-e", query,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise RuntimeError(f"SQL error: {result.stderr.strip()}")
        return result.stdout.strip()

    def _check(self, test_id: str, name: str, query: str,
               expected: str, tags: list[str] = None) -> bool:
        """Run a single verification check."""
        try:
            actual = self._run_sql(query)
            passed = str(actual) == str(expected)
            self.results.append({
                "id": test_id,
                "name": name,
                "status": "PASS" if passed else "FAIL",
                "expected": str(expected),
                "actual": str(actual),
                "tags": tags or [],
            })
            icon = "✅" if passed else "❌"
            print(f"  {icon} {test_id}: {name}")
            if not passed:
                print(f"     Expected: {expected}, Got: {actual}")
            return passed
        except Exception as e:
            self.results.append({
                "id": test_id,
                "name": name,
                "status": "ERROR",
                "error": str(e),
                "tags": tags or [],
            })
            print(f"  ⚠️  {test_id}: {name} — ERROR: {e}")
            return False

    def verify_all(self) -> dict:
        """Run all verification checks."""
        start = datetime.now()
        passed = 0
        failed = 0
        total = 0

        # ── 1. Table Counts ──
        print("\n═══ 1. Table Counts ═══")
        for table, expected_count in self.EXPECTED_COUNTS.items():
            total += 1
            ok = self._check(
                f"TC_SB_{total:02d}", f"{table} has {expected_count} rows",
                f"SELECT COUNT(*) FROM {table}",
                str(expected_count), ["schema", table],
            )
            if ok:
                passed += 1
            else:
                failed += 1

        # ── 2. LBF Registration ──
        print("\n═══ 2. LBF Form Registration ═══")
        for form_dir, form_name in [("LBFcpap", "CPAP"), ("LBFsleep", "Sleep Report")]:
            total += 1
            ok = self._check(
                f"TC_SB_{total:02d}", f"{form_name} form registered",
                f"SELECT COUNT(*) FROM registry WHERE directory = '{form_dir}'",
                "1", ["lbf", form_dir],
            )
            passed += ok
            failed += (not ok)

        # ── 3. Thai Patient Names (UTF-8) ──
        print("\n═══ 3. Patient Data (UTF-8) ═══")
        thai_checks = [
            (1001, "สมชาย", "ใจดี"),
            (1002, "สมหญิง", "รักษ์สุข"),
            (1003, "ประยุทธ์", "แข็งแรง"),
        ]
        for pid, fname, lname in thai_checks:
            total += 1
            ok = self._check(
                f"TC_SB_{total:02d}", f"Patient {pid}: {fname} {lname}",
                f"SELECT fname FROM patient_data WHERE pid = {pid}",
                fname, ["patient", "utf8"],
            )
            passed += ok
            failed += (not ok)

        # ── 4. Sleep Triage Verification ──
        print("\n═══ 4. Sleep Triage ═══")
        for form_id, (expected_triage, expected_ahi) in self.TRIAGE_CHECKS.items():
            total += 1
            ok = self._check(
                f"TC_SB_{total:02d}", f"Form {form_id} triage = {expected_triage}",
                f"SELECT field_value FROM lbf_data WHERE form_id = {form_id} AND field_id = 'triage_status'",
                expected_triage, ["triage", expected_triage],
            )
            passed += ok
            failed += (not ok)

            total += 1
            ok = self._check(
                f"TC_SB_{total:02d}", f"Form {form_id} AHI = {expected_ahi}",
                f"SELECT field_value FROM lbf_data WHERE form_id = {form_id} AND field_id = 'ahi'",
                expected_ahi, ["ahi"],
            )
            passed += ok
            failed += (not ok)

        # ── 5. Migration Log ──
        print("\n═══ 5. Migration Log ═══")
        for status, expected_count in [("success", 7), ("failed", 1), ("skipped", 1), ("pending", 1)]:
            total += 1
            ok = self._check(
                f"TC_SB_{total:02d}", f"migration_log {status} = {expected_count}",
                f"SELECT COUNT(*) FROM migration_log WHERE status = '{status}'",
                str(expected_count), ["migration", status],
            )
            passed += ok
            failed += (not ok)

        # ── 6. Idempotency ──
        print("\n═══ 6. Idempotency ═══")
        total += 1
        ok = self._check(
            f"TC_SB_{total:02d}", "All idempotency keys unique",
            "SELECT COUNT(DISTINCT idempotency_key) FROM migration_log",
            "10", ["idempotency"],
        )
        passed += ok
        failed += (not ok)

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)

        # ── Summary ──
        summary = {
            "suite": "Eir Sandbox DB Verification",
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
        }

        print(f"\n{'='*60}")
        print(f"⚖️  Forseti — Eir Sandbox Verification")
        print(f"   Total: {total}  |  ✅ Pass: {passed}  |  ❌ Fail: {failed}")
        print(f"   Pass Rate: {summary['pass_rate']}%")
        print(f"   Duration: {duration_ms}ms")
        print(f"{'='*60}")

        return summary

    def save_results(self, output_dir: str = "results") -> str:
        """Save results as JSON for Forseti dashboard."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eir_sandbox_verify_{timestamp}.json"
        filepath = Path(output_dir) / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Results saved: {filepath}")
        return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="⚖️ Eir Sandbox DB Verifier")
    parser.add_argument("--docker", default="asgard_mariadb", help="Docker container name")
    parser.add_argument("--user", default="openemr", help="DB user")
    parser.add_argument("--password", default="openemr", help="DB password")
    parser.add_argument("--database", default="openemr_sandbox", help="Database name")
    parser.add_argument("--output", default="results", help="Output directory")
    args = parser.parse_args()

    verifier = SandboxVerifier(
        docker_container=args.docker,
        db_user=args.user, db_pass=args.password,
        db_name=args.database,
    )

    summary = verifier.verify_all()
    verifier.save_results(args.output)

    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
