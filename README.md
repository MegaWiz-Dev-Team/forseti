# ⚖️ Forseti — LLM-Powered E2E Testing Service

> **Forseti** (ฟอร์เซที) — Norse god of justice and reconciliation, son of Baldr.
> An automated E2E testing service that uses LLM intelligence to test, analyze, and improve web applications.

[![Tests](https://img.shields.io/badge/unit_tests-111%2F111-brightgreen)]()
[![E2E](https://img.shields.io/badge/E2E-36%2F36_(100%25)-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![ISO](https://img.shields.io/badge/ISO-29110-orange)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 🏗️ Architecture

```
                    ┌─────────────────────────┐
                    │   forseti.yaml (multi)   │
                    │  ├─ csh-api (26 tests)   │
                    │  ├─ csh-ui  (5 tests)    │
                    │  └─ forseti-self (5 tests)│
                    └───────────┬───────────────┘
                                │
                    ┌───────────▼───────────────┐
                    │  ForsetiOrchestrator       │
                    │  1. Load YAML scenarios    │
                    │  2. Detect version (Git)   │
                    │  3. Auth (admin login)      │
                    │  4. Run API + UI tests      │
                    │  5. ReporterAgent           │
                    │     ├── SQLite DB           │
                    │     ├── ISO SI-04 report    │
                    │     ├── GitHub issue        │
                    │     └── FeedbackAgent (LLM) │
                    │         ├── 🔧 Backend      │
                    │         └── 🎨 UX/UI        │
                    └───────────┬───────────────┘
                                │
                    ┌───────────▼───────────────┐
                    │   Teal Theme Dashboard     │
                    │   http://localhost:5555     │
                    │   ├── Runs table + filter   │
                    │   ├── Version tracking      │
                    │   ├── Pass rate trend       │
                    │   └── LLM feedback modal    │
                    └───────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/MegaWiz-Dev-Team/forseti.git
cd forseti
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

### 2. Run Unit Tests

```bash
python -m pytest tests/ -v
# ✅ 111/111 passed
```

### 3. Run E2E Tests

```bash
# Terminal 1: Start target app (e.g. Cloud Super Hero)
cd /path/to/cloud-super-hero
GCP_PROJECT=cloud-super-hero-dev python server.py

# Terminal 2: Run Forseti E2E
cd /path/to/forseti
python run_e2e.py --project csh-student-ui
```

### 4. Start Dashboard

```bash
python dashboard.py
# ⚖️ Forseti Dashboard — http://localhost:5555
```

---

## ✨ Key Features

### Multi-Project E2E Testing
- **YAML-defined test scenarios** — ทั้ง API และ UI test
- **Multi-project support** — `forseti.yaml` กำหนดหลาย project
- **API testing** — HTTP methods (GET/POST/PUT) + status code assertions
- **UI testing** — Playwright browser automation via `type: "ui"` in YAML

### Intelligent Analysis (LLM-Powered)
- **🔧 Backend Expert Feedback** — API quality, error handling, security
- **🎨 UX/UI Expert Feedback** — Accessibility, user flow, error states
- **Gemini integration** — `gemini-2.0-flash` for action translation + analysis

### Version Tracking
- **Auto-detect** — Git SHA + tag อ่านอัตโนมัติจาก project directory
- **SemVer suggestion** — วิเคราะห์ git log แนะนำ version ตาม Conventional Commits
- **Create tags** — สร้าง git tag ผ่าน Forseti API

### Dashboard & Reporting
- **Real-time dashboard** — Teal theme dark mode + pass rate trend chart
- **SQLite persistence** — runs, scenarios, feedback tables
- **ISO SI-04 reports** — Auto-generated per run
- **GitHub issues** — Auto-create on test failures

---

## 📁 Project Structure

```
forseti/
├── src/forseti/
│   ├── agents/
│   │   ├── api_agent.py              # ADK API test agent (7 tools)
│   │   ├── feedback_agent.py         # LLM feedback (Backend + UX/UI)
│   │   ├── reporter_agent.py         # DB + ISO + GitHub + Feedback
│   │   └── orchestrator.py           # Main E2E pipeline
│   ├── tools/
│   │   ├── http_tools.py             # Async HTTP (GET/POST/PUT)
│   │   ├── assert_tools.py           # Status + JSON assertions
│   │   ├── auth_tools.py             # Admin login + OTP
│   │   ├── db_tools.py               # DB verification adapters
│   │   └── version_detector.py       # Git version detection + policy
│   ├── agent/
│   │   └── llm.py                    # Gemini/OpenAI LLM clients
│   ├── db/
│   │   └── results_db.py             # SQLite (runs + scenarios + feedback)
│   ├── reporter/
│   │   └── iso_report.py             # ISO SI-04 report generator
│   ├── models.py                     # Pydantic data models
│   ├── parser.py                     # YAML script parser
│   └── config.py                     # Settings (LLM, Browser, GitHub)
├── tests/                            # 111 TDD tests
│   ├── test_sprint01-06.py           # Sprint-organized test files
│   └── ...
├── web/dashboard/
│   └── index.html                    # Teal theme dashboard
├── docs/iso29110/                    # ISO 29110 documentation
├── reports/                          # Auto-generated reports
│   ├── SI-04_SIT_*.md                # ISO test reports
│   └── feedback/                     # LLM feedback per run
├── forseti.yaml                      # Multi-project config
├── forseti_results.db                # SQLite results DB
├── dashboard.py                      # Dashboard server (Flask)
└── run_e2e.py                        # E2E runner script
```

---

## 📊 Test Results Summary

### Unit Tests: 111/111 PASS ✅

| Sprint | Module | Tests |
|--------|--------|:-----:|
| SP1 | models, parser, config, collector | 34 |
| SP2 | http_tools, assert_tools, auth_tools, api_agent, iso_report, results_db | 27 |
| SP3 | reporter_agent, orchestrator | 10 |
| SP4 | multi-project, dashboard, self-test | 16 |
| SP5 | ui_testing, db_verify, version_detect | 7 |
| SP6 | version_policy, feedback_agent, feedback_db | 17 |

### E2E Tests: 36/36 PASS ✅

| Project | Scenarios | Pass Rate | Duration |
|---------|:---------:|:---------:|:--------:|
| Cloud Super Hero API | 26/26 | 100% | 9.4s |
| CSH Admin UI | 5/5 | 100% | 4.1s |
| Forseti Dashboard | 5/5 | 100% | 36ms |

---

## 📝 YAML Test Script Format

### API Test
```yaml
scenarios:
  - name: "TC_E2E_01 — Student Email Check"
    method: POST
    path: "/api/student/check-email"
    body:
      email: "test@example.com"
    expected_status: 200
    needs_auth: false
    tags: [registration, student]
```

### UI Test
```yaml
scenarios:
  - name: "Admin Dashboard — Login Page Loads"
    type: "ui"
    url: "http://localhost:8080/admin/login"
    actions:
      - navigate: "http://localhost:8080/admin/login"
      - assert_text: "Login"
    expected: "Login page renders correctly"
```

---

## 🔄 Version Management

Forseti auto-detects project version from Git and suggests next version:

```python
from forseti.tools.version_detector import suggest_next_version, create_version_tag

# Analyze git log → SemVer recommendation
result = suggest_next_version("/path/to/project")
# {"current": "v2.1.0", "suggested": "v2.2.0", "bump": "minor", ...}

# Create tag
create_version_tag("/path/to/project", "v2.2.0", message="Sprint 6 release")
```

| Commit Type | Version Bump |
|:-----------:|:------------:|
| `fix:` | PATCH |
| `feat:` | MINOR |
| `BREAKING CHANGE` | MAJOR |

---

## 🧠 LLM Feedback Agent

After each test run, Forseti generates expert feedback using Gemini:

```bash
export GEMINI_API_KEY="your-api-key"
python run_e2e.py --project csh-student-ui
```

| Expert | Focus |
|--------|-------|
| 🔧 Backend Expert | API quality, error handling, status codes, security |
| 🎨 UX/UI Expert | Accessibility, user flow, error states, forms |

Feedback is saved to:
- **SQLite** — `feedback` table linked to run_id
- **Markdown** — `reports/feedback/feedback_run{N}.md`
- **Dashboard** — Modal with severity badges (HIGH/MEDIUM/LOW)

---

## 📋 ISO 29110 Documentation

| Document | Description |
|----------|-------------|
| `PM-01_Project_Plan.md` | Project plan (6 sprints, 35 user stories) |
| `PM-02_SP0X_Status.md` | Sprint status reports (SP01—SP06) |
| `SI-01_Requirements.md` | Software requirements (SR-01 to SR-17) |
| `SI-04_SP0X_TestScript.md` | TDD test scripts per sprint (SP01—SP06) |
| `TRD-01` | Technical reference design |
| `BRD-01` | Business requirements document |

---

## 🔒 Safety

- **⛔ Production blocked** — Refuses to run against production environment
- **Dev only** — Targets `cloud-super-hero-dev` exclusively
- **Dry run** — Email tests use `dryRun: true`
- **Safe emails** — Mock students use `@test.invalid` domain

---

## 📅 Sprint Roadmap

| Sprint | Status | Focus | Tests |
|--------|:------:|-------|:-----:|
| SP1 | ✅ | Foundation (models, parser, CLI) | 34 |
| SP2 | ✅ | ADK multi-agent + API tools + SQLite | 27 |
| SP3 | ✅ | Reporter + Orchestrator + E2E 100% | 10 |
| SP4 | ✅ | Multi-project + Dashboard + Self-test | 16 |
| SP5 | ✅ | UI testing + DB verify + Version tracking | 7 |
| SP6 | ✅ | Version policy + LLM Feedback Agent | 17 |
| **Total** | **✅** | **6 Sprints Complete** | **111** |

---

*⚖️ Built by MegaWiz Dev Team — Ready for Asgard*
