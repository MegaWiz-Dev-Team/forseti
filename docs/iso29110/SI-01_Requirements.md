# SI-01: Software Requirements Specification
# ⚖️ Forseti — ข้อกำหนดความต้องการซอฟต์แวร์

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | SI-01 |
| **โครงการ** | Forseti |
| **อ้างอิง BRD** | BRD-01 |
| **มาตรฐาน** | ISO/IEC 29110 |
| **วันที่** | 2026-03-16 |

---

## 1. Requirement Traceability

| Req ID | BRD Ref | Component | Implementation | Test |
|---|---|---|---|---|
| SR-01 | FR-01 | `parser.py` | parse_script(), TestScript model | test_parser.py |
| SR-02 | FR-02 | `agent/llm.py` | GeminiClient.generate_actions() | (integration) |
| SR-03 | FR-03 | `browser/engine.py`, `agent/executor.py` | BrowserEngine, ActionExecutor | (integration) |
| SR-04 | FR-04 | `agent/llm.py` | GeminiClient.check_assertion() | (integration) |
| SR-05 | FR-05 | `reporter/collector.py` | ResultCollector.save_json() | test_collector.py |
| SR-06 | FR-06 | `reporter/html_report.py` | HTMLReportGenerator.generate() | (manual) |
| SR-07 | FR-07 | `reporter/github_issue.py` | GitHubIssueReporter.report_failures() | (integration) |
| SR-08 | FR-08 | `runner.py` | ForsetiRunner.run(dry_run=True) | (integration) |
| SR-09 | FR-09 | `agent/executor.py` | screenshot capture per step | (integration) |
| SR-10 | FR-10 | `agent/llm.py` | SelfHostedClient | test_config.py |

### Sprint 2 Requirements (ADK Multi-Agent)

| Req ID | User Story | Component | Implementation | Test |
|---|---|---|---|---|
| SR-11 | US-08 | `agents/` | ADK Agent (SequentialAgent, ParallelAgent) | test_api_agent.py |
| SR-12 | US-09 | `tools/http_tools.py` | http_get, http_post, http_put (httpx) | test_http_tools.py |
| SR-13 | US-10 | `tools/auth_tools.py` | admin_login, get_auth_headers | test_auth_tools.py |
| SR-14 | US-11 | `tools/assert_tools.py` | assert_status, assert_json_field | test_assert_tools.py |
| SR-15 | US-12 | `reporter/iso_report.py` | ISOReportGenerator → SI-04 markdown | test_iso_report.py |
| SR-16 | US-13 | `examples/test_scripts/` | cloud_super_hero_e2e.yaml | test_yaml_script.py |
| SR-17 | US-14 | `tests/` | Unit tests for all SP02 modules (TDD) | 28 tests total |

## 2. Data Models (SR-01)

```
TestScript
├── name: str
├── base_url: str
├── phase: SIT | UAT | REGRESSION
├── scenarios: list[TestScenario]
│   ├── name: str
│   ├── steps: list[TestStep]
│   │   ├── action: str (natural language)
│   │   └── screenshot: bool
│   ├── expected: str (natural language)
│   └── tags: list[str]
└── metadata: dict
```

### Sprint 2 — API Test Models (SR-11)

```
ApiTestStep
├── method: GET | POST | PUT | DELETE
├── path: str (relative to base_url)
├── body: dict (optional)
├── headers: dict (optional)
├── expected_status: int
├── expected_fields: dict (optional)
└── description: str

ApiScenario
├── name: str
├── steps: list[ApiTestStep]
├── auth_required: bool
└── tags: list[str]
```

## 3. LLM Translation Contract (SR-02)

**Input**: Natural language step (Thai/English)
**Output**: JSON array of `BrowserAction`:
```json
[
  {"type": "click", "selector": "button#login", "value": null, "description": "Click login"}
]
```

**Supported action types**: `navigate`, `click`, `type`, `select`, `wait`, `screenshot`, `assert_text`, `assert_element`, `scroll`, `hover`

## 4. Assertion Contract (SR-04)

**Input**: Expected result (NL) + page text content
**Output**:
```json
{"passed": true, "reason": "Dashboard text visible", "evidence": "Welcome admin"}
```

## 5. Report Format (SR-06)

HTML report ประกอบด้วย:
- Pass rate % (card)
- Progress bar (pass/fail/error/skip)
- Collapsible scenario details
- Step-by-step results with screenshots
- Phase indicator (SIT/UAT)

### Sprint 2 — ISO Report Format (SR-15)

SI-04 markdown report ประกอบด้วย:
- Header table (เอกสาร, Sprint, วันที่, Environment)
- Test matrix table (TC ID, Test Case, Expected, Actual, Status)
- Summary (total, passed, failed, pass rate)
- Duration + timestamp

## 6. GitHub Issue Format (SR-07)

Title: `⚖️ [Forseti] Test Failed: {scenario_name} ({phase})`
Body:
- Test suite name, phase, URL, timestamp
- Step-by-step results with ✅/❌ icons
- Expected vs actual result
- Error message (code block)
- Labels: `bug`, `e2e-test-failure`

## 7. ADK Agent Architecture (SR-11)

```
ForsetiOrchestrator (SequentialAgent)
├── ParallelTestRunner (ParallelAgent)
│   ├── ApiTestAgent (Agent + tools)
│   └── UiTestAgent (Agent + Playwright tools)
├── ReporterAgent (Agent + report tools)
└── AnalyzerAgent (Agent + LLM analysis)

Model: gemini-3.1-flash-lite-preview
```
