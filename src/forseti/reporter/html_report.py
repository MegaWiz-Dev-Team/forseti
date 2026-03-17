"""HTML report generator using Jinja2."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, select_autoescape

from forseti.models import TestSuiteResult

logger = logging.getLogger("forseti.reporter.html_report")

# Fallback inline template when template file is not found
INLINE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚖️ Forseti Report — {{ suite.script.name }}</title>
    <style>
        :root {
            --bg: #0f172a; --surface: #1e293b; --border: #334155;
            --text: #e2e8f0; --muted: #94a3b8;
            --pass: #22c55e; --fail: #ef4444; --error: #f59e0b; --skip: #6366f1;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; }
        .container { max-width: 1100px; margin: 0 auto; }
        h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
        .subtitle { color: var(--muted); margin-bottom: 2rem; font-size: 0.9rem; }

        /* Summary Cards */
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.2rem; text-align: center; }
        .card .value { font-size: 2rem; font-weight: 700; }
        .card .label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; margin-top: 0.3rem; }
        .card.pass .value { color: var(--pass); }
        .card.fail .value { color: var(--fail); }
        .card.error .value { color: var(--error); }
        .card.rate .value { color: var(--pass); }

        /* Progress bar */
        .progress-bar { background: var(--surface); border-radius: 8px; height: 24px; overflow: hidden; margin-bottom: 2rem; display: flex; }
        .progress-bar .segment { height: 100%; transition: width 0.5s; }
        .progress-bar .pass-seg { background: var(--pass); }
        .progress-bar .fail-seg { background: var(--fail); }
        .progress-bar .error-seg { background: var(--error); }
        .progress-bar .skip-seg { background: var(--skip); }

        /* Scenario list */
        .scenario { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 1rem; overflow: hidden; }
        .scenario-header { padding: 1rem 1.2rem; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
        .scenario-header:hover { background: rgba(255,255,255,0.03); }
        .scenario-name { font-weight: 600; }
        .badge { padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .badge-pass { background: rgba(34,197,94,0.15); color: var(--pass); }
        .badge-fail { background: rgba(239,68,68,0.15); color: var(--fail); }
        .badge-error { background: rgba(245,158,11,0.15); color: var(--error); }
        .badge-skip { background: rgba(99,102,241,0.15); color: var(--skip); }
        .scenario-details { padding: 0 1.2rem 1.2rem; border-top: 1px solid var(--border); }
        .step { padding: 0.6rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.9rem; }
        .step:last-child { border-bottom: none; }
        .step-status { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 0.5rem; }
        .step-status.pass { background: var(--pass); }
        .step-status.fail { background: var(--fail); }
        .step-status.error { background: var(--error); }
        .expected { margin-top: 0.8rem; padding: 0.8rem; background: rgba(255,255,255,0.03); border-radius: 8px; font-size: 0.85rem; }
        .expected label { color: var(--muted); font-size: 0.75rem; display: block; margin-bottom: 0.3rem; }
        .error-msg { color: var(--fail); font-size: 0.85rem; margin-top: 0.5rem; padding: 0.5rem; background: rgba(239,68,68,0.1); border-radius: 6px; }
        .screenshot-img { max-width: 100%; border-radius: 8px; margin-top: 0.5rem; border: 1px solid var(--border); }

        .footer { text-align: center; color: var(--muted); font-size: 0.8rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); }
    </style>
</head>
<body>
<div class="container">
    <h1>⚖️ Forseti — {{ suite.script.name }}</h1>
    <div class="subtitle">
        Phase: <strong>{{ suite.script.phase.value }}</strong> &nbsp;|&nbsp;
        URL: {{ suite.script.base_url }} &nbsp;|&nbsp;
        {{ summary.started_at }}
    </div>

    <div class="summary">
        <div class="card rate">
            <div class="value">{{ "%.1f"|format(suite.pass_rate) }}%</div>
            <div class="label">Pass Rate</div>
        </div>
        <div class="card">
            <div class="value">{{ suite.total }}</div>
            <div class="label">Total</div>
        </div>
        <div class="card pass">
            <div class="value">{{ suite.passed }}</div>
            <div class="label">Passed</div>
        </div>
        <div class="card fail">
            <div class="value">{{ suite.failed }}</div>
            <div class="label">Failed</div>
        </div>
        <div class="card error">
            <div class="value">{{ suite.errors }}</div>
            <div class="label">Errors</div>
        </div>
    </div>

    <div class="progress-bar">
        {% if suite.total > 0 %}
        <div class="segment pass-seg" style="width: {{ suite.passed / suite.total * 100 }}%"></div>
        <div class="segment fail-seg" style="width: {{ suite.failed / suite.total * 100 }}%"></div>
        <div class="segment error-seg" style="width: {{ suite.errors / suite.total * 100 }}%"></div>
        <div class="segment skip-seg" style="width: {{ suite.skipped / suite.total * 100 }}%"></div>
        {% endif %}
    </div>

    {% for sr in suite.scenario_results %}
    <div class="scenario">
        <div class="scenario-header" onclick="this.parentElement.classList.toggle('open')">
            <span class="scenario-name">{{ sr.scenario.name }}</span>
            <span class="badge badge-{{ sr.status.value }}">{{ sr.status.value }}</span>
        </div>
        <div class="scenario-details">
            {% for step_r in sr.step_results %}
            <div class="step">
                <span class="step-status {{ step_r.status.value }}"></span>
                {{ step_r.step.action }}
                {% if step_r.duration_ms %}<span style="color:var(--muted);font-size:0.75rem"> ({{ step_r.duration_ms }}ms)</span>{% endif %}
            </div>
            {% endfor %}

            <div class="expected">
                <label>Expected Result:</label>
                {{ sr.scenario.expected }}
            </div>

            {% if sr.assertion_result %}
            <div class="expected">
                <label>Assertion:</label>
                {{ sr.assertion_result }}
            </div>
            {% endif %}

            {% if sr.error_message %}
            <div class="error-msg">❌ {{ sr.error_message }}</div>
            {% endif %}
        </div>
    </div>
    {% endfor %}

    <div class="footer">
        Generated by ⚖️ Forseti v0.1.0 — {{ now }}
    </div>
</div>
<script>
    document.querySelectorAll('.scenario').forEach(el => {
        const details = el.querySelector('.scenario-details');
        details.style.display = 'none';
        el.querySelector('.scenario-header').addEventListener('click', () => {
            details.style.display = details.style.display === 'none' ? 'block' : 'none';
        });
    });
</script>
</body>
</html>
"""


class HTMLReportGenerator:
    """Generates HTML reports from test results."""

    def __init__(self, output_dir: str = "reports", templates_dir: str | None = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir = templates_dir

    def generate(self, result: TestSuiteResult, filename: str | None = None) -> Path:
        """Generate an HTML report.

        Args:
            result: Test suite result data.
            filename: Optional output filename.

        Returns:
            Path to the generated HTML report.
        """
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            phase = result.script.phase.value
            filename = f"forseti_report_{phase}_{ts}.html"

        # Try to load template from file, fall back to inline
        template_str = INLINE_TEMPLATE
        if self.templates_dir:
            template_path = Path(self.templates_dir) / "report.html"
            if template_path.exists():
                template_str = template_path.read_text(encoding="utf-8")

        env = Environment(autoescape=select_autoescape(["html"]))
        template = env.from_string(template_str)

        from forseti.reporter.collector import ResultCollector

        collector = ResultCollector()
        summary = collector.get_summary(result)

        html = template.render(
            suite=result,
            summary=summary,
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        path = self.output_dir / filename
        path.write_text(html, encoding="utf-8")
        logger.info(f"📊 HTML report generated: {path}")
        return path
