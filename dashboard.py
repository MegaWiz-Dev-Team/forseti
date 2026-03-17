"""⚖️ Forseti Web Report Dashboard — serve test results from SQLite."""
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).parent / "src"))
from forseti.db.results_db import ResultsDB

app = Flask(__name__, static_folder="web/dashboard")
DB_PATH = "forseti_results.db"


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


if __name__ == "__main__":
    print("⚖️ Forseti Dashboard — http://localhost:5555")
    app.run(host="0.0.0.0", port=5555, debug=True)
