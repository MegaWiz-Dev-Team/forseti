#!/usr/bin/env python3
"""Parse pytest junit XML and POST aggregated results to Forseti /api/runs.

Designed to bridge external pytest suites (Bifrost, Mimir, Eir, etc.) into the
Forseti dashboard so every test run — Forseti's own YAML scenarios and any
service's pytest output — lives in one place.

Usage:
    python junit_to_forseti.py \
        --junit results.xml \
        --suite bifrost-pytest \
        --phase SIT \
        --base-url http://bifrost.asgard-services.svc:8000 \
        --commit "$GITHUB_SHA" \
        --version "$GITHUB_REF_NAME" \
        --forseti-url http://localhost:5555
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request
import json
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_junit(path: Path) -> dict:
    """Read pytest junit XML and return a Forseti `/api/runs` payload skeleton.

    Pytest can emit either a single <testsuite> root or a <testsuites> wrapper;
    we handle both. Each <testcase> becomes one scenario.
    """
    tree = ET.parse(path)
    root = tree.getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))

    total = passed = failed = errors = skipped = 0
    duration_ms = 0
    scenarios: list[dict] = []

    for suite in suites:
        total += int(suite.attrib.get("tests", 0) or 0)
        failed += int(suite.attrib.get("failures", 0) or 0)
        errors += int(suite.attrib.get("errors", 0) or 0)
        skipped += int(suite.attrib.get("skipped", 0) or 0)
        try:
            duration_ms += int(float(suite.attrib.get("time", "0")) * 1000)
        except (TypeError, ValueError):
            pass

        for case in suite.findall("testcase"):
            name = f"{case.attrib.get('classname', '')}::{case.attrib.get('name', '')}".strip(":")
            try:
                case_ms = int(float(case.attrib.get("time", "0")) * 1000)
            except (TypeError, ValueError):
                case_ms = 0

            failure = case.find("failure")
            error = case.find("error")
            skipped_elem = case.find("skipped")
            if failure is not None:
                status, error_message = "failed", failure.attrib.get("message") or (failure.text or "")[:500]
            elif error is not None:
                status, error_message = "error", error.attrib.get("message") or (error.text or "")[:500]
            elif skipped_elem is not None:
                status, error_message = "skipped", skipped_elem.attrib.get("message") or None
            else:
                status, error_message = "passed", None

            scenarios.append(
                {
                    "name": name,
                    "status": status,
                    "duration_ms": case_ms,
                    "error_message": error_message,
                }
            )

    passed = total - failed - errors - skipped
    return {
        "total": total,
        "passed": max(0, passed),
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "duration_ms": duration_ms,
        "scenarios": scenarios,
    }


def post_run(forseti_url: str, payload: dict, timeout: float = 30.0) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{forseti_url.rstrip('/')}/api/runs",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--junit", required=True, type=Path, help="Path to pytest junit XML")
    p.add_argument("--suite", required=True, help="Suite name shown in dashboard (e.g. bifrost-pytest)")
    p.add_argument("--phase", default="SIT", choices=["SIT", "UAT", "PROD", "DEV"], help="Pipeline phase tag")
    p.add_argument("--base-url", default="", help="Service base URL under test")
    p.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "unknown"))
    p.add_argument("--version", default=os.environ.get("GITHUB_REF_NAME", "unknown"))
    p.add_argument(
        "--forseti-url",
        default=os.environ.get("FORSETI_URL", "http://localhost:5555"),
        help="Forseti dashboard URL (also reads FORSETI_URL env)",
    )
    p.add_argument("--dry-run", action="store_true", help="Print payload, do not POST")
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    if not args.junit.exists():
        print(f"junit file not found: {args.junit}", file=sys.stderr)
        return 2

    parsed = parse_junit(args.junit)
    payload = {
        "suite_name": args.suite,
        "phase": args.phase,
        "base_url": args.base_url,
        "project_commit": args.commit,
        "project_version": args.version,
        **parsed,
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    try:
        result = post_run(args.forseti_url, payload)
    except urllib.error.HTTPError as e:
        print(f"Forseti rejected payload: HTTP {e.code} {e.reason}\n{e.read().decode('utf-8', 'ignore')}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Could not reach Forseti at {args.forseti_url}: {e.reason}", file=sys.stderr)
        return 1

    print(
        f"Forseti run #{result.get('id')} saved · "
        f"{parsed['passed']}/{parsed['total']} passed · "
        f"{parsed['failed']} failed · {parsed['errors']} errors · {parsed['skipped']} skipped"
    )
    return 0 if parsed["failed"] == 0 and parsed["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
