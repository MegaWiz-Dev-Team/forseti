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

## 6. GitHub Issue Format (SR-07)

Title: `⚖️ [Forseti] Test Failed: {scenario_name} ({phase})`
Body:
- Test suite name, phase, URL, timestamp
- Step-by-step results with ✅/❌ icons
- Expected vs actual result
- Error message (code block)
- Labels: `bug`, `e2e-test-failure`
