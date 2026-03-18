"""⚖️ Forseti Web Report Dashboard — serve test results from SQLite."""
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).parent / "src"))
from forseti.db.results_db import ResultsDB

app = Flask(__name__, static_folder="web/dashboard")
DB_PATH = os.environ.get("DB_PATH", "/app/data/forseti_results.db")


def get_db():
    """Create a fresh DB connection per request (thread-safe)."""
    return ResultsDB(db_path=DB_PATH)


@app.route("/")
def index():
    return send_from_directory("web/dashboard", "index.html")


@app.route("/api/suites")
def api_suites():
    db = get_db()
    suites = db.get_suites()
    db.close()
    return jsonify(suites)


@app.route("/api/runs")
def api_runs():
    suite = request.args.get("suite")
    db = get_db()
    runs = db.get_runs(limit=50, suite=suite)
    db.close()
    return jsonify(runs)


@app.route("/api/runs/<int:run_id>")
def api_run_detail(run_id):
    db = get_db()
    run = db.get_run(run_id)
    db.close()
    if not run:
        return jsonify({"error": "Not found"}), 404
    return jsonify(run)


@app.route("/api/trend")
def api_trend():
    suite = request.args.get("suite")
    db = get_db()
    trend = db.get_trend(limit=20, suite=suite)
    db.close()
    return jsonify(trend)


@app.route("/api/runs/<int:run_id>/feedback")
def api_run_feedback(run_id):
    db = get_db()
    feedback = db.get_feedback(run_id)
    db.close()
    return jsonify(feedback)


@app.route("/api/runs", methods=["POST"])
def api_submit_run():
    """Accept external test results (unit/e2e/ui) from any Asgard service."""
    data = request.get_json(force=True)
    if not data or "suite_name" not in data:
        return jsonify({"error": "suite_name required"}), 400

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
    return jsonify({"id": run_id, "status": "saved"}), 201


if __name__ == "__main__":
    print("⚖️ Forseti Dashboard — http://localhost:5555")
    app.run(host="0.0.0.0", port=5555, debug=True)
