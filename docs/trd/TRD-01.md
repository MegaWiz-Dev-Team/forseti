# TRD-01: Technical Requirements Document
# ⚖️ Forseti — LLM-Powered E2E Testing Service

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | TRD-01 |
| **โครงการ** | Forseti (ฟอร์เซตี) |
| **เวอร์ชัน** | 1.0 |
| **วันที่** | 2026-03-16 |
| **อ้างอิง BRD** | BRD-01 |

---

## 1. Technology Stack

| Component | Technology | เหตุผล |
|---|---|---|
| Language | Python 3.11+ | ภาษาหลักตาม requirement |
| Browser Automation | Playwright (Python) | Modern, fast, multi-browser |
| LLM — Primary | Google Gemini 2.0 Flash | Unlimited budget, Thai support ดี |
| LLM — Self-hosted | OpenAI-compatible API | รองรับ Ollama, vLLM, etc. |
| Data Models | Pydantic v2 | Validation + serialization |
| CLI | Click + Rich | Developer-friendly |
| Test Script | YAML (PyYAML) | Human-readable, Thai support |
| Reporting | Jinja2 | HTML template engine |
| GitHub Integration | PyGithub | REST API client |
| HTTP Client | httpx | Async-ready for self-hosted LLM |
| Testing | pytest + pytest-asyncio | TDD methodology |
| Linting | Ruff | Fast Python linter |

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          CLI Layer                           │
│  forseti run | forseti validate | forseti report | forseti info│
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    ForsetiRunner                             │
│  Orchestrates: Parser → LLM → Executor → Collector → Report │
└──────┬──────────┬──────────┬──────────┬─────────────────────┘
       ▼          ▼          ▼          ▼
  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
  │ Parser │ │  LLM   │ │Browser │ │ Reporter │
  │ (YAML) │ │ Agent  │ │ Engine │ │          │
  └────────┘ └───┬────┘ └───┬────┘ └──┬───┬───┘
                 ▼          ▼         ▼   ▼
            ┌────────┐ ┌────────┐ ┌────┐┌──────┐
            │ Gemini │ │Playwrt │ │JSON││GitHub│
            │  API   │ │        │ │HTML││Issue │
            └────────┘ └────────┘ └────┘└──────┘
```

## 3. Module Specifications

### 3.1 `models.py` — Data Models
- `TestStep`, `TestScenario`, `TestScript` — test script structure
- `BrowserAction`, `ActionPlan` — LLM output structure
- `StepResult`, `ScenarioResult`, `TestSuiteResult` — execution results
- ใช้ Pydantic v2 สำหรับ validation และ JSON serialization

### 3.2 `parser.py` — YAML Parser
- รองรับ 2 formats: string shorthand (`"click button"`) และ dict (`{action: "...", screenshot: false}`)
- `validate_script()` สำหรับ syntax validation ก่อน run

### 3.3 `agent/llm.py` — LLM Client
- **System Prompt** ออกแบบมาเพื่อ translate Thai/English NL → JSON browser actions
- **Assertion Prompt** ตรวจสอบ expected result จาก page content
- Factory pattern: `create_llm_client(config)` → `GeminiClient` or `SelfHostedClient`
- Response parsing: extract JSON จาก markdown code blocks

### 3.4 `agent/executor.py` — Action Executor
- Pattern matching (`match/case`) สำหรับ action types
- Comma-separated selector fallback (LLM อาจให้หลาย CSS selectors)
- Screenshot capture: ทุก step + error screenshot
- Timing measurement ต่อ step

### 3.5 `browser/engine.py` — Browser Engine
- Playwright lifecycle management
- `session()` async context manager
- Video recording support (optional)

### 3.6 `reporter/` — Reporting
- **collector.py**: JSON persistence, summary stats
- **html_report.py**: Dark-theme HTML report, progress bar, collapsible scenarios
- **github_issue.py**: Auto-create formatted issues with step details + evidence

### 3.7 `runner.py` — Pipeline Orchestrator
- Full pipeline: Parse → Navigate → LLM translate → Execute → Assert → Report
- dry-run mode: LLM translation only, no browser
- Console summary output

## 4. Data Flow

```
YAML Script → parse_script() → TestScript
    ↓
ForsetiRunner.run()
    ↓
For each scenario:
    ↓
    For each step:
        step.action → LLM.generate_actions() → ActionPlan
            ↓
        ActionExecutor.execute_plan() → StepResult
    ↓
    scenario.expected → LLM.check_assertion() → pass/fail
    ↓
    ScenarioResult
    ↓
TestSuiteResult
    ↓
├── ResultCollector.save_json()     → results/forseti_SIT_*.json
├── HTMLReportGenerator.generate()  → reports/forseti_report_*.html
└── GitHubIssueReporter.report()   → GitHub Issues (if fail)
```

## 5. Configuration & Environment

| Env Variable | คำอธิบาย | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API Key | Yes (if using Gemini) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | For issue creation |
| `GITHUB_REPO` | Target repo (`owner/repo`) | For issue creation |
| `FORSETI_LLM_PROVIDER` | `gemini` or `openai_compatible` | No (default: gemini) |
| `FORSETI_LLM_MODEL` | Model name | No (default: gemini-2.0-flash) |
| `FORSETI_LLM_BASE_URL` | Self-hosted LLM endpoint | For self-hosted only |
| `FORSETI_HEADED` | Set to run browser in headed mode | No |

## 6. TDD Approach

ดำเนินการพัฒนาตาม Test-Driven Development:

1. **Red**: เขียน test ก่อน — กำหนด expected behavior
2. **Green**: implement code ให้ test ผ่าน
3. **Refactor**: ปรับปรุง code โดย test ยังผ่าน

### Test Suites (Sprint 1)

| Test File | จำนวน Tests | Coverage |
|---|---|---|
| `test_models.py` | 11 | Data models, pass rate calculation |
| `test_parser.py` | 8 | YAML parsing, validation |
| `test_config.py` | 9 | Config loading, env vars |
| `test_collector.py` | 3 | JSON save/load, summary |
| **Total** | **34** | Core modules |

## 7. Deployment

```bash
# 1. Clone repository
git clone <repo-url> && cd forseti

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install
pip install -e ".[dev]"
playwright install chromium

# 4. Configure
export GEMINI_API_KEY="your-key"
export GITHUB_TOKEN="your-token"  # optional
export GITHUB_REPO="owner/repo"   # optional

# 5. Run tests
forseti run examples/test_scripts/login_test.yaml
```
